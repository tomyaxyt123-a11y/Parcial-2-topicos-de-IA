"""
Trazabilidad y auditoría de envíos (SQLite).

Guarda un registro por cada certificado procesado: evento, rol, persona,
correo, estado y detalle. Permite:

  * Evitar reenvíos duplicados (`ya_enviado`).
  * Auditar qué se envió, falló o quedó pendiente.
  * Reportar estadísticas por evento y por dependencia.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import config

LOG = logging.getLogger("certificado")

_CANDADO = threading.Lock()

ESQUEMA_EVENTOS = """
CREATE TABLE IF NOT EXISTS eventos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    dependencia     TEXT,
    archivo_origen  TEXT,
    fecha_creacion  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total           INTEGER DEFAULT 0,
    ok              INTEGER DEFAULT 0,
    error           INTEGER DEFAULT 0,
    omitido         INTEGER DEFAULT 0
);
"""

ESQUEMA_ENVIOS = """
CREATE TABLE IF NOT EXISTS envios (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    evento   TEXT NOT NULL,
    rol      TEXT,
    nombre   TEXT,
    correo   TEXT,
    estado   TEXT,
    detalle  TEXT,
    fecha    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INDICE_CORREO = "CREATE INDEX IF NOT EXISTS idx_envios_correo ON envios(correo);"
INDICE_EVENTO = "CREATE INDEX IF NOT EXISTS idx_envios_evento ON envios(evento);"


def ruta_db() -> Path:
    """Ruta del archivo SQLite (configurable con la variable DB_PATH)."""
    return Path(config.DB_PATH)


def conectar() -> sqlite3.Connection:
    """Abre una conexión SQLite lista para usar."""
    conexion = sqlite3.connect(str(ruta_db()), timeout=15, check_same_thread=False)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA journal_mode=WAL;")
    return conexion


def inicializar_db() -> None:
    """Crea las tablas e índices si no existen."""
    with _CANDADO:
        conexion = conectar()
        try:
            conexion.execute(ESQUEMA_EVENTOS)
            conexion.execute(ESQUEMA_ENVIOS)
            conexion.execute(INDICE_CORREO)
            conexion.execute(INDICE_EVENTO)
            conexion.commit()
        finally:
            conexion.close()
    LOG.info("Base de datos lista en %s", ruta_db())


def registrar_envio(
    evento: str,
    rol: str,
    nombre: str,
    correo: str,
    estado: str,
    detalle: str = "",
) -> int:
    """Registra un envío en la base de datos y devuelve el id generado."""
    with _CANDADO:
        conexion = conectar()
        try:
            cursor = conexion.execute(
                """INSERT INTO envios (evento, rol, nombre, correo, estado, detalle, fecha)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    evento,
                    rol,
                    nombre,
                    correo,
                    estado,
                    detalle,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conexion.commit()
            identificador = int(cursor.lastrowid)
        finally:
            conexion.close()
    LOG.info("Registro #%d insertado (%s - %s)", identificador, correo, estado)
    return identificador


def ya_enviado(evento: str, correo: str) -> bool:
    """Indica si el evento+correo ya fue enviado exitosamente.

    Evita reenvíos del mismo evento al mismo participante.
    """
    correo = (correo or "").strip().lower()
    if not correo:
        return False
    with _CANDADO:
        conexion = conectar()
        try:
            fila = conexion.execute(
                "SELECT COUNT(*) AS total FROM envios "
                "WHERE evento = ? AND LOWER(TRIM(correo)) = ? AND estado = 'OK'",
                (evento, correo),
            ).fetchone()
        finally:
            conexion.close()
    return bool(fila and fila["total"] > 0)


def registrar_evento(
    nombre: str,
    dependencia: str = "",
    archivo_origen: str = "",
    total: int = 0,
    ok: int = 0,
    error: int = 0,
    omitido: int = 0,
) -> None:
    """Crea o actualiza el resumen de un evento."""
    with _CANDADO:
        conexion = conectar()
        try:
            existente = conexion.execute(
                "SELECT id FROM eventos WHERE nombre = ?", (nombre,)
            ).fetchone()
            if existente:
                conexion.execute(
                    """UPDATE eventos SET dependencia = ?, archivo_origen = ?, total = ?,
                       ok = ?, error = ?, omitido = ? WHERE id = ?""",
                    (dependencia, archivo_origen, total, ok, error, omitido, existente["id"]),
                )
            else:
                conexion.execute(
                    """INSERT INTO eventos (nombre, dependencia, archivo_origen, total, ok, error, omitido)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nombre, dependencia, archivo_origen, total, ok, error, omitido),
                )
            conexion.commit()
        finally:
            conexion.close()


def listar_eventos(limite: int = 50) -> List[Dict[str, object]]:
    """Lista los eventos registrados (más recientes primero)."""
    with _CANDADO:
        conexion = conectar()
        try:
            filas = conexion.execute(
                "SELECT * FROM eventos ORDER BY id DESC LIMIT ?", (limite,)
            ).fetchall()
        finally:
            conexion.close()
    return [dict(fila) for fila in filas]


def listar_envios(
    evento: Optional[str] = None,
    estado: Optional[str] = None,
    limite: int = 200,
) -> List[Dict[str, object]]:
    """Lista los envíos con filtros opcionales por evento y estado."""
    consulta = "SELECT * FROM envios"
    condiciones: List[str] = []
    parametros: List[object] = []

    if evento:
        condiciones.append("evento = ?")
        parametros.append(evento)
    if estado:
        condiciones.append("estado = ?")
        parametros.append(estado)

    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)
    consulta += " ORDER BY id DESC LIMIT ?"
    parametros.append(limite)

    with _CANDADO:
        conexion = conectar()
        try:
            filas = conexion.execute(consulta, parametros).fetchall()
        finally:
            conexion.close()
    return [dict(fila) for fila in filas]


def estadisticas(evento: Optional[str] = None) -> Dict[str, object]:
    """Calcula estadísticas de envíos (globales o de un evento)."""
    with _CANDADO:
        conexion = conectar()
        try:
            if evento:
                filas = conexion.execute(
                    "SELECT estado, COUNT(*) AS total FROM envios WHERE evento = ? GROUP BY estado",
                    (evento,),
                ).fetchall()
                por_rol = conexion.execute(
                    "SELECT rol, COUNT(*) AS total FROM envios WHERE evento = ? GROUP BY rol",
                    (evento,),
                ).fetchall()
            else:
                filas = conexion.execute(
                    "SELECT estado, COUNT(*) AS total FROM envios GROUP BY estado"
                ).fetchall()
                por_rol = conexion.execute(
                    "SELECT rol, COUNT(*) AS total FROM envios GROUP BY rol"
                ).fetchall()
        finally:
            conexion.close()

    resumen = {"OK": 0, "ERROR": 0, "OMITIDO": 0}
    for fila in filas:
        resumen[str(fila["estado"])] = int(fila["total"])

    return {
        "evento": evento or "todos",
        "total": sum(resumen.values()),
        "por_estado": resumen,
        "por_rol": {str(f["rol"]): int(f["total"]) for f in por_rol},
    }


def limpiar_evento(evento: str) -> int:
    """Elimina los registros de un evento (uso administrativo)."""
    with _CANDADO:
        conexion = conectar()
        try:
            cursor = conexion.execute("DELETE FROM envios WHERE evento = ?", (evento,))
            conexion.execute("DELETE FROM eventos WHERE nombre = ?", (evento,))
            conexion.commit()
            return int(cursor.rowcount)
        finally:
            conexion.close()


def purgar_registros(dias: int = 30) -> int:
    """Elimina los envíos con más de `dias` días (retención de datos personales).

    Returns:
        Cantidad de registros eliminados.
    """
    if dias <= 0:
        return 0
    limite = (datetime.now() - timedelta(days=dias)).isoformat(timespec="seconds")
    with _CANDADO:
        conexion = conectar()
        try:
            cursor = conexion.execute("DELETE FROM envios WHERE fecha < ?", (limite,))
            conexion.commit()
            eliminados = int(cursor.rowcount)
        finally:
            conexion.close()
    if eliminados:
        LOG.info("Purgados %d registros de trazabilidad anteriores a %d días", eliminados, dias)
    return eliminados
