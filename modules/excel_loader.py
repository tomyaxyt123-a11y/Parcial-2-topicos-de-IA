"""
Carga y validación del archivo Excel de participantes.

El archivo debe contener **5 hojas**: Asistentes, Ponentes, Conferenciantes,
Evaluadores y Organizadores. Cada hoja tiene sus campos mínimos (ver
`CAMPOS_POR_ROL`), pero los encabezados pueden venir con sinónimos
(`"Email"` en lugar de `"correo"`); el módulo de IA se encarga de mapearlos.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from modules import ia_validator

LOG = logging.getLogger("certificado")

HOJAS_REQUERIDAS: List[str] = [
    "Asistentes",
    "Ponentes",
    "Conferenciantes",
    "Evaluadores",
    "Organizadores",
]

CAMPOS_POR_ROL: Dict[str, List[str]] = {
    "Asistentes": ["nombres", "apellidos", "correo"],
    "Ponentes": ["nombres", "apellidos", "correo", "documento", "ponencia"],
    "Conferenciantes": ["nombres", "apellidos", "correo", "documento", "conferencia"],
    "Evaluadores": ["nombres", "apellidos", "correo", "documento"],
    "Organizadores": ["nombres", "apellidos", "correo"],
}

# Campo que describe la participación específica de cada rol
CAMPO_APORTE_ROL: Dict[str, str] = {
    "Asistentes": None,
    "Ponentes": "ponencia",
    "Conferenciantes": "conferencia",
    "Evaluadores": None,
    "Organizadores": None,
}


class ExcelInvalidoError(ValueError):
    """Error de negocio: el Excel no cumple el formato esperado."""


def cargar_excel(ruta: str, flexible: bool = False) -> Dict[str, pd.DataFrame]:
    """Carga un archivo Excel y devuelve un diccionario por hoja.

    Args:
        ruta: ruta al archivo .xlsx
        flexible: si es True, tolera mayúsculas/minúsculas, hojas individuales o
                  subconjuntos de hojas requeridas. Si es False (por defecto),
                  exige exactamente las 5 hojas requeridas.
    """
    ruta = str(ruta)
    if not Path(ruta).exists():
        raise ExcelInvalidoError(f"No se encontró el archivo: {ruta}")

    try:
        xls = pd.ExcelFile(ruta)
    except Exception as exc:  # archivo corrupto o con extensión incorrecta
        raise ExcelInvalidoError(f"No fue posible leer el archivo Excel: {exc}") from exc

    if not flexible:
        hojas_existentes = [h for h in xls.sheet_names if h in HOJAS_REQUERIDAS]
        faltantes = [h for h in HOJAS_REQUERIDAS if h not in hojas_existentes]

        if faltantes:
            raise ExcelInvalidoError(
                "Faltan hojas requeridas. "
                f"Encontradas: {hojas_existentes or 'ninguna'}. Faltantes: {faltantes}"
            )

        LOG.info("Hojas detectadas: %d/%d OK", len(hojas_existentes), len(HOJAS_REQUERIDAS))

        datos: Dict[str, pd.DataFrame] = {}
        for hoja in HOJAS_REQUERIDAS:
            df = pd.read_excel(xls, sheet_name=hoja)
            df.columns = [str(c).strip() for c in df.columns]
            datos[hoja] = df
        return datos

    # Modo flexible para la interfaz web:
    nombres_hojas = list(xls.sheet_names)
    datos_flex: Dict[str, pd.DataFrame] = {h: pd.DataFrame() for h in HOJAS_REQUERIDAS}

    SINONIMOS_HOJAS = {
        "Asistentes": ["asistente", "asistentes", "participante", "participantes", "estudiante", "estudiantes", "inscrito", "inscritos", "publico", "asistencia"],
        "Ponentes": ["ponente", "ponentes", "expositor", "expositores", "autor", "autores", "presentador", "presentadores"],
        "Conferenciantes": ["conferenciante", "conferenciantes", "conferencista", "conferencistas", "invitado", "invitados", "keynote"],
        "Evaluadores": ["evaluador", "evaluadores", "jurado", "jurados", "comite cientifico", "revisores", "juez", "jueces"],
        "Organizadores": ["organizador", "organizadores", "logistica", "staff", "comite organizador"],
    }

    asignadas = set()
    for hoja_real in nombres_hojas:
        hoja_limpia = ia_validator.normalizar_texto(hoja_real).lower()
        rol_encontrado = None
        for rol, sinonimos in SINONIMOS_HOJAS.items():
            if rol not in asignadas and any(s in hoja_limpia for s in sinonimos):
                rol_encontrado = rol
                break
        if rol_encontrado:
            df = pd.read_excel(xls, sheet_name=hoja_real)
            df.columns = [str(c).strip() for c in df.columns]
            datos_flex[rol_encontrado] = df
            asignadas.add(rol_encontrado)

    # Si ninguna hoja coincidió y hay al menos una hoja (ej. "Hoja 1", "Sheet1", etc.)
    if not asignadas and nombres_hojas:
        primera = nombres_hojas[0]
        df = pd.read_excel(xls, sheet_name=primera)
        df.columns = [str(c).strip() for c in df.columns]
        datos_flex["Asistentes"] = df
        asignadas.add("Asistentes")

    # Si Asistentes quedó vacío pero hay hojas no asignadas disponibles:
    if "Asistentes" not in asignadas:
        for hoja_real in nombres_hojas:
            df = pd.read_excel(xls, sheet_name=hoja_real)
            df.columns = [str(c).strip() for c in df.columns]
            datos_flex["Asistentes"] = df
            asignadas.add("Asistentes")
            break

    total_filas = sum(len(df) for df in datos_flex.values() if df is not None and not df.empty)
    if total_filas == 0:
        raise ExcelInvalidoError("El archivo Excel no contiene filas con datos de participantes.")

    LOG.info("Hojas detectadas (modo flexible): asignadas %s con %d registros totales", list(asignadas), total_filas)
    return datos_flex


def mapear_encabezados_hojas(
    datos: Dict[str, pd.DataFrame],
    umbral: int = 85,
) -> Tuple[Dict[str, pd.DataFrame], List[Dict[str, object]]]:
    """Normaliza los encabezados de cada hoja a los campos canónicos.

    Devuelve los DataFrames ya renombrados y un reporte de las equivalencias
    detectadas (evidencia del módulo de PLN semántico).
    """
    datos_mapeados: Dict[str, pd.DataFrame] = {}
    reporte: List[Dict[str, object]] = []

    for rol, df in datos.items():
        if df is None or df.empty:
            datos_mapeados[rol] = df
            continue
        mapeo = ia_validator.mapear_encabezados(df.columns, umbral=umbral)
        if mapeo:
            for original, canonico in mapeo.items():
                reporte.append(
                    {
                        "rol": rol,
                        "columna_original": original,
                        "columna_canonica": canonico,
                        "metodo": "exacto" if original.strip().lower() == canonico else "similitud",
                    }
                )
        datos_mapeados[rol] = df.rename(columns=mapeo)

    if reporte:
        LOG.info("[IA] %d encabezados remapeados a campos canónicos", len(reporte))
    return datos_mapeados, reporte


def _campos_efectivos(df: pd.DataFrame, umbral: int = 85) -> set:
    """Campos canónicos disponibles en el DataFrame (con o sin mapeo)."""
    if df is None or df.empty:
        return set()
    disponibles = {str(c).strip().lower() for c in df.columns}
    for original, canonico in ia_validator.mapear_encabezados(df.columns, umbral=umbral).items():
        disponibles.add(canonico)
    return disponibles


def validar_campos(datos: Dict[str, pd.DataFrame], umbral: int = 85) -> List[str]:
    """Valida que cada hoja contenga los campos mínimos de su rol.

    Devuelve la lista de errores (vacía si todo es correcto).
    """
    errores: List[str] = []
    total_con_datos = 0

    for rol, df in datos.items():
        if df is None or df.empty:
            continue
        total_con_datos += 1
        disponibles = _campos_efectivos(df, umbral)
        
        # Debe tener columna de nombre
        tiene_nombre = (
            "nombres" in disponibles
            or "nombre" in disponibles
            or any("nombre" in str(c).lower() or "name" in str(c).lower() for c in df.columns)
        )
        if not tiene_nombre:
            errores.append(f"Hoja '{rol}' requiere una columna con el nombre ('nombres' o 'nombre')")

        # Debe tener columna de correo
        tiene_correo = (
            "correo" in disponibles
            or any("correo" in str(c).lower() or "mail" in str(c).lower() for c in df.columns)
        )
        if not tiene_correo:
            errores.append(f"Hoja '{rol}' requiere una columna de correo electrónico ('correo' o 'email')")

    if total_con_datos == 0:
        errores.append("El archivo Excel no contiene filas con datos de participantes en ninguna hoja.")

    return errores


def _columna_para(df: pd.DataFrame, canonico: str, umbral: int = 85) -> Optional[str]:
    """Devuelve el encabezado real que corresponde a un campo canónico."""
    if canonico in df.columns:
        return canonico
    mapeo = ia_validator.mapear_encabezados(df.columns, umbral=umbral)
    for original, mapeado in mapeo.items():
        if mapeado == canonico:
            return original
    return None


def _valor(df: pd.DataFrame, fila: int, canonico: str, umbral: int = 85) -> str:
    """Lee un campo canónico de una fila como texto limpio."""
    columna = _columna_para(df, canonico, umbral)
    if columna is None:
        return ""
    valor = df.iloc[fila].get(columna, "")
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def extraer_participantes(
    datos: Dict[str, pd.DataFrame],
    umbral: int = 85,
) -> List[Dict[str, object]]:
    """Convierte las hojas en una lista unificada de participantes.

    Cada registro incluye el rol, los campos canónicos, el nombre completo
    normalizado y las anomalías detectadas por el módulo de IA.
    """
    participantes: List[Dict[str, object]] = []

    for rol, df in datos.items():
        if df is None or df.empty:
            LOG.info("Hoja '%s' sin registros", rol)
            continue

        for indice in range(len(df)):
            registro: Dict[str, object] = {
                "rol": rol,
                "nombres": ia_validator.normalizar_nombre(_valor(df, indice, "nombres", umbral)),
                "apellidos": ia_validator.normalizar_nombre(_valor(df, indice, "apellidos", umbral)),
                "correo": ia_validator.normalizar_correo(_valor(df, indice, "correo", umbral)),
                "documento": _valor(df, indice, "documento", umbral),
                "institucion": _valor(df, indice, "institucion", umbral),
                "cargo": _valor(df, indice, "cargo", umbral),
                "fila_excel": indice + 2,  # +2: encabezado + base 1
            }

            aporte = CAMPO_APORTE_ROL.get(rol)
            if aporte:
                registro[aporte] = _valor(df, indice, aporte, umbral)

            registro["nombre_completo"] = ia_validator.normalizar_nombre_completo(
                registro["nombres"], registro["apellidos"]
            )
            registro["anomalias"] = ia_validator.detectar_anomalias(registro)
            participantes.append(registro)

    return participantes


def resumen_carga(datos: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """Devuelve el número de registros por hoja."""
    return {rol: int(len(df)) for rol, df in datos.items()}


def verificar_hojas(datos: Dict[str, pd.DataFrame]) -> List[str]:
    """Lista las hojas requeridas que no están presentes (vacía si están todas)."""
    return [hoja for hoja in HOJAS_REQUERIDAS if hoja not in datos]
