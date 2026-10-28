"""
Certificado Unilasallista - Punto de entrada (Flask).

Flujo principal expuesto en `POST /procesar`:

    Carga Excel -> Validación IA -> Plantilla -> Generar PDF -> Envío SMTP -> Registro

API:
    GET  /                    Interfaz web de operación
    POST /procesar            Procesa un evento completo
    GET  /api/estado          Estado del sistema (SMTP, base de datos)
    GET  /api/eventos         Eventos registrados
    GET  /api/envios          Trazabilidad de envíos (filtros: evento, estado)
    GET  /api/plantillas      Plantillas PDF disponibles
    GET  /health              Sonda de disponibilidad
"""

from __future__ import annotations

import io
import logging
import os
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, jsonify, render_template, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

import config
from modules import excel_loader, ia_validator, mail_service, pdf_generator, pptx_filler, tracker

LOG = logging.getLogger("certificado")

app = Flask(
    __name__,
    template_folder=str(config.TEMPLATES_DIR),
    static_folder=str(config.STATIC_DIR),
    static_url_path="/static",
)
app.config.from_object(config.Config)

MAX_UPLOAD_MB = config.MAX_CONTENT_LENGTH / (1024 * 1024)


# ==========================================================================
# Utilidades
# ==========================================================================
def _validar_plantilla(ruta: Optional[str]) -> Optional[str]:
    """Valida que la plantilla exista y esté dentro del proyecto."""
    if not ruta or str(ruta).strip() == "":
        candidata_pptx = config.BASE_DIR / "Certificados.pptx"
        if candidata_pptx.exists():
            return str(candidata_pptx)
        candidata = config.TEMPLATES_DIR / "certificado_base.pdf"
        return str(candidata) if candidata.exists() else None

    # Si es el archivo oficial por defecto
    if str(ruta).strip() == "Certificados.pptx":
        candidata_pptx = config.BASE_DIR / "Certificados.pptx"
        if candidata_pptx.exists():
            return str(candidata_pptx)

    raiz = config.BASE_DIR.resolve()
    candidata = Path(ruta)
    if not candidata.is_absolute():
        en_templates = config.TEMPLATES_DIR / candidata
        if en_templates.exists():
            candidata = en_templates
        else:
            candidata = config.BASE_DIR / candidata
    try:
        resuelta = candidata.resolve()
    except OSError:
        return None
    if raiz not in resuelta.parents and resuelta != raiz:
        LOG.info("[PDF] Ruta de plantilla fuera del proyecto: %s", ruta)
        return None

    return str(resuelta) if resuelta.exists() else None


def _contrasena_pdf(participante: Dict[str, object]) -> str:
    """Contraseña del PDF: número de documento o valor por defecto."""
    documento = str(participante.get("documento") or "").strip()
    if documento:
        return documento
    return str(config.PDF_PASSWORD or "").strip()


def _limpiar_temporales(archivos: List[str], conservar: Optional[str] = None) -> None:
    """Elimina únicamente los archivos temporales generados en TMP_DIR (conserva OUT_DIR)."""
    if not config.LIMPIAR_TEMPORALES:
        return
    for archivo in archivos:
        try:
            ruta = Path(archivo)
            if conservar and ruta.name == Path(conservar).name:
                continue
            if ruta.exists() and ruta.parent.resolve() == config.TMP_DIR.resolve():
                ruta.unlink()
        except OSError:
            pass


# ==========================================================================
# Lógica de negocio reutilizable (también usada por las pruebas)
# ==========================================================================
def procesar_evento(
    archivo_excel: str,
    evento: str,
    plantilla: Optional[str] = None,
    dependencia: str = "",
    enviar: bool = True,
    forzar_envio_real: bool = False,
    ignorar_ya_enviados: bool = True,
) -> Dict[str, object]:
    """Ejecuta el flujo completo para un evento y devuelve el reporte.

    Args:
        archivo_excel: ruta del archivo `.xlsx` con las 5 hojas.
        evento: nombre del evento (se usa como clave de trazabilidad).
        plantilla: ruta del PDF base a usar como fondo.
        dependencia: dependencia organizadora (para la trazabilidad).
        enviar: si es `False` solo genera los PDF sin enviar correos.
        forzar_envio_real: si es `True` transmite correos omitiendo la simulación.
        ignorar_ya_enviados: si es `True` regenera certificados aunque ya existan.

    Returns:
        ``{'ok': bool, 'total': int, 'detalle': {...}}``
    """
    detalle: Dict[str, object] = {
        "evento": evento,
        "dependencia": dependencia,
        "resumen_carga": {},
        "mapeo_encabezados": [],
        "duplicados": {},
        "anomalias": {},
        "roles": {},
        "errores": [],
        "omitidos": [],
        "enviados": [],
        "fallidos": [],
        "zip_url": None,
    }

    # ------------------------------------------------------------------
    # 1. Carga del Excel
    # ------------------------------------------------------------------
    try:
        datos = excel_loader.cargar_excel(archivo_excel, flexible=True)
    except excel_loader.ExcelInvalidoError as exc:
        detalle["errores"].append(str(exc))
        LOG.info("[INFO] Error de carga: %s", exc)
        return {"ok": False, "total": 0, "detalle": detalle}

    # ------------------------------------------------------------------
    # 2. Validación con IA (mapeo semántico de encabezados + campos)
    # ------------------------------------------------------------------
    datos, mapeo = excel_loader.mapear_encabezados_hojas(datos, config.UMBRAL_ENCABEZADO)
    detalle["mapeo_encabezados"] = mapeo

    errores_campos = excel_loader.validar_campos(datos, config.UMBRAL_ENCABEZADO)
    if errores_campos:
        detalle["errores"].extend(errores_campos)
        LOG.info("[INFO] Validación fallida: %s", "; ".join(errores_campos))
        return {"ok": False, "total": 0, "detalle": detalle}

    detalle["resumen_carga"] = excel_loader.resumen_carga(datos)

    participantes = excel_loader.extraer_participantes(datos, config.UMBRAL_ENCABEZADO)
    detalle["total_participantes"] = len(participantes)

    # ------------------------------------------------------------------
    # 3. Detección de duplicados y anomalías por rol
    # ------------------------------------------------------------------
    for rol, df in datos.items():
        duplicados_correo = ia_validator.detectar_duplicados(
            df, config.UMBRAL_SIMILITUD, columna="correo"
        )
        duplicados_nombre = ia_validator.detectar_duplicados_por_nombre(df, config.UMBRAL_SIMILITUD)
        if duplicados_correo or duplicados_nombre:
            detalle["duplicados"][rol] = {
                "por_correo": ia_validator.resumir_duplicados(duplicados_correo, df, "correo"),
                "por_nombre": ia_validator.resumir_duplicados(duplicados_nombre, df, "nombres"),
            }
            LOG.info(
                "[IA] Detectados %d posibles duplicados en %s",
                len(duplicados_correo) + len(duplicados_nombre),
                rol,
            )

    anomalias_por_rol: Dict[str, List[Dict[str, object]]] = {}
    for participante in participantes:
        if participante.get("anomalias"):
            anomalias_por_rol.setdefault(str(participante["rol"]), []).append(
                {
                    "nombre": participante.get("nombre_completo"),
                    "correo": participante.get("correo"),
                    "anomalias": participante["anomalias"],
                }
            )
    detalle["anomalias"] = anomalias_por_rol

    # ------------------------------------------------------------------
    # 4. Filtrado, generación de PDF, envío y registro
    # ------------------------------------------------------------------
    plantilla_valida = _validar_plantilla(plantilla)
    archivos_generados: List[str] = []

    totales = {"total": 0, "ok": 0, "error": 0, "omitido": 0}

    if plantilla_valida:
        es_pptx = Path(plantilla_valida).suffix.lower() == ".pptx"
    else:
        candidata_pptx = config.BASE_DIR / "Certificados.pptx"
        if candidata_pptx.exists():
            es_pptx = True
            plantilla_valida = str(candidata_pptx)
        else:
            es_pptx = False
            plantilla_valida = str(config.TEMPLATES_DIR / "certificado_base.pdf")

    detalle["plantilla_utilizada"] = Path(plantilla_valida).name if plantilla_valida else "Certificados.pptx"

    evento_seguro = secure_filename(evento or "evento") or "evento"
    carpeta_evento = config.OUT_DIR / evento_seguro
    carpeta_evento.mkdir(parents=True, exist_ok=True)

    # 4.1 Filtrar participantes y descartar no válidos o ya enviados
    participantes_validos = []
    for participante in participantes:
        totales["total"] += 1
        rol = str(participante.get("rol", ""))
        correo = str(participante.get("correo", ""))
        nombre = str(participante.get("nombre_completo", ""))

        if not ignorar_ya_enviados and tracker.ya_enviado(evento, correo):
            totales["omitido"] += 1
            detalle["omitidos"].append({"nombre": nombre, "correo": correo, "rol": rol})
            tracker.registrar_envio(
                evento, rol, nombre, correo, "OMITIDO", "Ya enviado para este evento"
            )
            continue

        if not ia_validator.validar_correo_ia(correo):
            totales["error"] += 1
            detalle["fallidos"].append(
                {"nombre": nombre, "correo": correo, "rol": rol, "detalle": "Correo inválido"}
            )
            tracker.registrar_envio(evento, rol, nombre, correo, "ERROR", "Correo inválido")
            continue

        participantes_validos.append(participante)

    # 4.2 Llenar plantillas PPTX en memoria (ultra rápido)
    rutas_pptx_a_convertir = []
    items_preparados = []

    for participante in participantes_validos:
        nombre = str(participante.get("nombre_completo", ""))
        slug = "_".join(nombre.title().split()) or "participante"
        datos_pdf = dict(participante)
        datos_pdf["evento"] = evento
        datos_pdf.setdefault("fecha", pdf_generator.formatear_fecha_es())

        if es_pptx and plantilla_valida and Path(plantilla_valida).exists():
            res_gen = pptx_filler.generar_pptx_incietec(
                datos_pdf, carpeta_evento, slug, ruta_plantilla=plantilla_valida
            )
            rutas_pptx_a_convertir.append(res_gen["pptx"])
            items_preparados.append((participante, datos_pdf, Path(res_gen["pdf"]), res_gen["nombre_pdf"], res_gen["nombre_pptx"], True))
        else:
            nombre_pdf = f"{uuid.uuid4().hex[:8]}_{slug}.pdf"
            ruta_pdf = carpeta_evento / nombre_pdf
            items_preparados.append((participante, datos_pdf, ruta_pdf, nombre_pdf, None, False))

    # 4.3 Conversión por lotes en UN SOLO proceso de PowerPoint (optimización clave)
    if rutas_pptx_a_convertir:
        pptx_filler.convertir_lote_pptx_a_pdf(rutas_pptx_a_convertir)

    # 4.4 Verificación de PDF, protección y envío
    for participante, datos_pdf, ruta_pdf, nombre_pdf, nombre_pptx, era_pptx in items_preparados:
        rol = str(participante.get("rol", ""))
        correo = str(participante.get("correo", ""))
        nombre = str(participante.get("nombre_completo", ""))

        try:
            if not ruta_pdf.exists():
                fondo_a_usar = None
                if plantilla_valida and Path(plantilla_valida).suffix.lower() == ".pdf" and Path(plantilla_valida).exists():
                    fondo_a_usar = plantilla_valida
                else:
                    plantilla_fondo = config.TEMPLATES_DIR / "Certificados.pdf"
                    if not plantilla_fondo.exists():
                        plantilla_fondo = config.TEMPLATES_DIR / "certificado_base.pdf"
                    fondo_a_usar = str(plantilla_fondo) if plantilla_fondo.exists() else None

                pdf_generator.generar_certificado(
                    datos_pdf,
                    fondo_a_usar,
                    str(ruta_pdf),
                    proteger=config.PROTEGER_PDF,
                    contrasena=_contrasena_pdf(participante),
                )
            elif config.PROTEGER_PDF:
                clave = _contrasena_pdf(participante)
                if clave:
                    pdf_generator._cifrar_pdf(str(ruta_pdf), clave)

            archivos_generados.append(str(ruta_pdf))
        except Exception as exc:
            totales["error"] += 1
            detalle["fallidos"].append(
                {"nombre": nombre, "correo": correo, "rol": rol, "detalle": f"Error PDF: {exc}"}
            )
            tracker.registrar_envio(evento, rol, nombre, correo, "ERROR", f"Error PDF: {exc}")
            continue

        url_descarga = f"/descargar-pdf/{evento_seguro}/{nombre_pdf}"
        url_descarga_pptx = (
            f"/descargar-pdf/{evento_seguro}/{nombre_pptx}" if nombre_pptx else None
        )

        # 4.5 Envío por SMTP
        if not enviar:
            totales["ok"] += 1
            detalle["enviados"].append(
                {
                    "nombre": nombre,
                    "correo": correo,
                    "rol": rol,
                    "detalle": "Certificado generado (sin envío)",
                    "archivo": nombre_pdf,
                    "descarga": url_descarga,
                    "descarga_pptx": url_descarga_pptx,
                }
            )
            tracker.registrar_envio(evento, rol, nombre, correo, "OK", "Certificado generado (sin envío)")
            continue

        resultado = mail_service.enviar_certificado(
            correo, nombre, str(ruta_pdf), evento, rol, forzar_real=forzar_envio_real
        )
        estado = str(resultado["estado"])
        if estado == "OK":
            totales["ok"] += 1
            detalle["enviados"].append(
                {
                    "nombre": nombre,
                    "correo": correo,
                    "rol": rol,
                    "detalle": resultado["detalle"],
                    "archivo": nombre_pdf,
                    "descarga": url_descarga,
                    "descarga_pptx": url_descarga_pptx,
                }
            )
        else:
            totales["error"] += 1
            detalle["fallidos"].append(
                {"nombre": nombre, "correo": correo, "rol": rol, "detalle": resultado["detalle"]}
            )
        tracker.registrar_envio(evento, rol, nombre, correo, estado, str(resultado["detalle"]))

    detalle["roles"] = totales
    evento_seguro = secure_filename(evento or "evento") or "evento"
    detalle["zip_url"] = f"/descargar-zip/{evento_seguro}"

    tracker.registrar_evento(
        evento,
        dependencia=dependencia,
        archivo_origen=Path(archivo_excel).name,
        total=totales["total"],
        ok=totales["ok"],
        error=totales["error"],
        omitido=totales["omitido"],
    )

    LOG.info(
        "[INFO] Total procesados: %d | OK: %d | ERROR: %d | OMITIDO: %d",
        totales["total"], totales["ok"], totales["error"], totales["omitido"],
    )

    _limpiar_temporales(archivos_generados)

    return {"ok": True, "total": totales["total"], "detalle": detalle}


# ==========================================================================
# Rutas
# ==========================================================================
@app.route("/")
def index():
    """Interfaz web de operación."""
    return render_template(
        "index.html",
        hojas=excel_loader.HOJAS_REQUERIDAS,
        smtp_configurado=mail_service.smtp_configurado(),
        smtp_host=config.SMTP_HOST,
        smtp_puerto=config.SMTP_PORT,
        simulacion=mail_service.envio_simulado(),
        eventos=tracker.listar_eventos(limite=10),
        plantilla=str(config.TEMPLATES_DIR / "certificado_base.pdf"),
    )


@app.route("/descargar-ejemplo")
def descargar_ejemplo():
    """Descarga el archivo Excel de ejemplo."""
    return send_from_directory(
        directory=str(config.DATA_DIR),
        path="ejemplo_evento.xlsx",
        as_attachment=True,
    )


@app.route("/descargar-plantilla-guia")
def descargar_plantilla_guia():
    """Descarga la plantilla guía oficial editable (.pptx o .pdf) con los placeholders institucionales."""
    nombre_archivo = request.args.get("archivo", "Certificados.pptx")
    ruta = config.BASE_DIR / secure_filename(nombre_archivo)
    if not ruta.exists():
        ruta = config.TEMPLATES_DIR / secure_filename(nombre_archivo)
    if not ruta.exists():
        ruta = config.BASE_DIR / "Certificados.pptx"
    if not ruta.exists():
        return jsonify({"ok": False, "error": "No se encontró el archivo de plantilla guía"}), 404

    nombre_descarga = (
        "Plantilla_Guia_Certificados_Unilasallista.pptx"
        if ruta.suffix.lower() == ".pptx"
        else f"Plantilla_Guia_{ruta.name}"
    )

    mime = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        if ruta.suffix.lower() == ".pptx"
        else "application/pdf"
    )

    return send_file(
        str(ruta),
        as_attachment=True,
        download_name=nombre_descarga,
        mimetype=mime,
    )


@app.route("/procesar", methods=["POST"])
def procesar():
    """Procesa un evento: carga el Excel, valida, genera PDF y envía."""
    evento = (request.form.get("evento") or "").strip()
    dependencia = (request.form.get("dependencia") or "").strip()
    plantilla = request.form.get("plantilla") or None
    enviar_real = str(request.form.get("enviar_real", "")).strip().lower() in {"1", "true", "on", "yes"}
    # Todo certificado creado debe ser procesado y enviado sí o sí
    ignorar_ya_enviados = True
    archivo = request.files.get("excel")

    if not evento:
        return jsonify({"ok": False, "total": 0, "error": "El nombre del evento es obligatorio"}), 400

    if archivo is None or not archivo.filename:
        return jsonify({"ok": False, "total": 0, "error": "Debe adjuntar el archivo Excel"}), 400

    extension = Path(archivo.filename).suffix.lower()
    if extension not in {".xlsx", ".xlsm"}:
        return jsonify(
            {"ok": False, "total": 0, "error": "Formato no soportado: use un archivo .xlsx"}
        ), 400

    nombre_seguro = secure_filename(archivo.filename) or "evento.xlsx"
    ruta_guardada = config.TMP_DIR / f"{uuid.uuid4().hex[:8]}_{nombre_seguro}"
    archivo.save(str(ruta_guardada))
    LOG.info("[INFO] Cargando archivo: %s", nombre_seguro)

    try:
        resultado = procesar_evento(
            str(ruta_guardada),
            evento,
            plantilla=plantilla,
            dependencia=dependencia,
            forzar_envio_real=enviar_real,
            ignorar_ya_enviados=ignorar_ya_enviados,
        )
    finally:
        try:
            ruta_guardada.unlink(missing_ok=True)
        except OSError:
            pass

    if not resultado["ok"]:
        errores = resultado["detalle"].get("errores") or ["Error desconocido"]
        return jsonify({"ok": False, "total": 0, "error": "; ".join(errores)}), 422

    return jsonify(resultado)


@app.route("/descargar-pdf/<evento>/<archivo>")
def descargar_pdf(evento, archivo):
    """Permite ver o descargar un certificado PDF generado."""
    carpeta = config.OUT_DIR / secure_filename(evento)
    archivo_seguro = secure_filename(archivo)
    return send_from_directory(str(carpeta), archivo_seguro, as_attachment=False)


@app.route("/descargar-zip/<evento>")
def descargar_zip(evento):
    """Empaqueta y descarga todos los certificados generados para un evento en un archivo ZIP."""
    carpeta = config.OUT_DIR / secure_filename(evento)
    if not carpeta.exists():
        return jsonify({"ok": False, "error": "No hay certificados para este evento"}), 404

    archivos_pdf = list(carpeta.glob("*.pdf"))
    if not archivos_pdf:
        return jsonify({"ok": False, "error": "No se encontraron certificados en la carpeta"}), 404

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for pdf in archivos_pdf:
            zip_file.write(pdf, arcname=pdf.name)
    buffer.seek(0)

    nombre_zip = f"Certificados_{secure_filename(evento)}.zip"
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=nombre_zip,
    )


@app.route("/api/enviar-individual", methods=["POST"])
def api_enviar_individual():
    """Envía un certificado específico al correo ingresado por el usuario."""
    datos = request.get_json(silent=True) or request.form
    destinatario = (datos.get("destinatario") or "").strip()
    nombre = (datos.get("nombre") or "").strip()
    evento = (datos.get("evento") or "").strip()
    rol = (datos.get("rol") or "Participante").strip()
    archivo = (datos.get("archivo") or "").strip()

    if not destinatario or not ia_validator.validar_correo_ia(destinatario):
        return jsonify({"ok": False, "error": f"El correo «{destinatario}» no tiene un formato válido"}), 400

    if not archivo:
        return jsonify({"ok": False, "error": "No se indicó el archivo del certificado"}), 400

    evento_seguro = secure_filename(evento or "evento")
    ruta_pdf = config.OUT_DIR / evento_seguro / secure_filename(archivo)
    if not ruta_pdf.exists():
        ruta_pdf = config.OUT_DIR / secure_filename(archivo)
    if not ruta_pdf.exists():
        ruta_pdf = config.TMP_DIR / secure_filename(archivo)
    if not ruta_pdf.exists():
        return jsonify({"ok": False, "error": f"Archivo no encontrado: {archivo}"}), 404

    es_real = mail_service.smtp_configurado() and not mail_service.envio_simulado()
    try:
        resultado = mail_service.enviar_certificado(
            destinatario=destinatario,
            nombre=nombre,
            archivo_pdf=str(ruta_pdf),
            evento=evento,
            rol=rol,
            forzar_real=es_real,
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Error al enviar: {exc}"}), 500

    if resultado["estado"] == "OK":
        detalle_envio = resultado["detalle"]
        if not es_real:
            mensaje_usuario = f"Envío simulado exitoso a {destinatario}."
        else:
            mensaje_usuario = f"Certificado enviado exitosamente por correo institucional a {destinatario}."
        tracker.registrar_envio(evento, rol, nombre, destinatario, "OK", f"Envío manual: {detalle_envio}")
        return jsonify({
            "ok": True,
            "mensaje": mensaje_usuario,
            "detalle": detalle_envio,
            "es_real": es_real,
        })
    else:
        return jsonify({"ok": False, "error": resultado["detalle"]}), 400


@app.route("/api/historial")
def api_historial():
    """Devuelve el historial completo de eventos guardados con sus certificados y archivos."""
    eventos = tracker.listar_eventos(limite=50)
    resultado = []
    for ev in eventos:
        nombre = ev.get("nombre") or ""
        evento_seguro = secure_filename(nombre)
        carpeta = config.OUT_DIR / evento_seguro

        # Archivos generados en disco
        pdfs_en_disco = {}
        pptx_en_disco = {}
        if carpeta.exists():
            for p in carpeta.glob("*.pdf"):
                pdfs_en_disco[p.stem.lower()] = p.name
            for p in carpeta.glob("*.pptx"):
                pptx_en_disco[p.stem.lower()] = p.name

        envios = tracker.listar_envios(evento=nombre, limite=200)
        participantes = []
        for env in envios:
            nom_part = env.get("nombre") or ""
            slug = "_".join(nom_part.title().split()).lower()
            archivo_pdf = None
            archivo_pptx = None
            for stem_lower, fname in pdfs_en_disco.items():
                if slug in stem_lower or stem_lower in slug:
                    archivo_pdf = fname
                    break
            for stem_lower, fname in pptx_en_disco.items():
                if slug in stem_lower or stem_lower in slug:
                    archivo_pptx = fname
                    break

            participantes.append({
                "id": env.get("id"),
                "nombre": nom_part,
                "correo": env.get("correo"),
                "rol": env.get("rol"),
                "estado": env.get("estado"),
                "detalle": env.get("detalle"),
                "fecha": env.get("fecha"),
                "archivo_pdf": archivo_pdf,
                "descarga_pdf": f"/descargar-pdf/{evento_seguro}/{archivo_pdf}" if archivo_pdf else None,
                "descarga_pptx": f"/descargar-pdf/{evento_seguro}/{archivo_pptx}" if archivo_pptx else None,
            })

        tiene_archivos = bool(carpeta.exists() and list(carpeta.glob("*.pdf")))
        resultado.append({
            "id": ev.get("id"),
            "nombre": nombre,
            "dependencia": ev.get("dependencia"),
            "archivo_origen": ev.get("archivo_origen"),
            "fecha": ev.get("fecha_creacion"),
            "total": ev.get("total", 0),
            "ok": ev.get("ok", 0),
            "error": ev.get("error", 0),
            "omitido": ev.get("omitido", 0),
            "zip_url": f"/descargar-zip/{evento_seguro}" if tiene_archivos else None,
            "participantes": participantes,
            "total_guardados": len(participantes),
        })

    return jsonify({"ok": True, "historial": resultado})


def actualizar_config_remitente(
    nuevo_correo: str,
    nuevo_nombre: Optional[str] = None,
    nueva_clave: Optional[str] = None,
) -> None:
    """Actualiza dinámicamente el correo, nombre y credencial SMTP en memoria y los persiste en .env."""
    import re
    nuevo_correo = (nuevo_correo or "").strip()
    config.SMTP_FROM = nuevo_correo
    os.environ["SMTP_FROM"] = nuevo_correo

    # En la mayoría de proveedores (Office 365, Gmail) el usuario de login SMTP coincide con el correo
    config.SMTP_USER = nuevo_correo
    os.environ["SMTP_USER"] = nuevo_correo

    if nuevo_nombre is not None and str(nuevo_nombre).strip():
        config.SMTP_FROM_NAME = str(nuevo_nombre).strip()
        os.environ["SMTP_FROM_NAME"] = config.SMTP_FROM_NAME

    clave_limpia = str(nueva_clave).strip() if nueva_clave is not None else ""
    if clave_limpia:
        config.SMTP_PASS = clave_limpia
        os.environ["SMTP_PASS"] = clave_limpia

    env_path = config.BASE_DIR / ".env"
    if env_path.exists():
        try:
            contenido = env_path.read_text(encoding="utf-8")

            # SMTP_FROM
            if "SMTP_FROM=" in contenido:
                contenido = re.sub(r"^SMTP_FROM=.*$", f"SMTP_FROM={config.SMTP_FROM}", contenido, flags=re.MULTILINE)
            else:
                contenido += f"\nSMTP_FROM={config.SMTP_FROM}\n"

            # SMTP_USER
            if "SMTP_USER=" in contenido:
                contenido = re.sub(r"^SMTP_USER=.*$", f"SMTP_USER={config.SMTP_USER}", contenido, flags=re.MULTILINE)
            else:
                contenido += f"\nSMTP_USER={config.SMTP_USER}\n"

            # SMTP_FROM_NAME
            if "SMTP_FROM_NAME=" in contenido:
                contenido = re.sub(r"^SMTP_FROM_NAME=.*$", f"SMTP_FROM_NAME={config.SMTP_FROM_NAME}", contenido, flags=re.MULTILINE)
            else:
                contenido += f"\nSMTP_FROM_NAME={config.SMTP_FROM_NAME}\n"

            # SMTP_PASS si se suministró una nueva
            if clave_limpia:
                if "SMTP_PASS=" in contenido:
                    contenido = re.sub(r"^SMTP_PASS=.*$", f"SMTP_PASS={config.SMTP_PASS}", contenido, flags=re.MULTILINE)
                else:
                    contenido += f"\nSMTP_PASS={config.SMTP_PASS}\n"

            env_path.write_text(contenido, encoding="utf-8")
            LOG.info("[SMTP] Remitente y credenciales actualizados en memoria y en .env: %s <%s>", config.SMTP_FROM_NAME, config.SMTP_FROM)
        except Exception as exc:
            LOG.warning("[SMTP] No fue posible persistir en .env: %s", exc)


@app.route("/api/configuracion-correo", methods=["GET", "POST"])
def api_configuracion_correo():
    """Consulta o actualiza dinámicamente el correo remitente, contraseña y nombre institucional del sistema."""
    tiene_clave = bool(config.SMTP_PASS and str(config.SMTP_PASS).strip())

    if request.method == "POST":
        datos = request.get_json(silent=True) or request.form
        nuevo_correo = (datos.get("smtp_from") or datos.get("correo") or "").strip()
        nuevo_nombre = datos.get("smtp_from_name") or datos.get("nombre")
        nueva_clave = datos.get("smtp_pass") or datos.get("password") or datos.get("clave")

        if not nuevo_correo:
            return jsonify({"ok": False, "error": "El correo del remitente es obligatorio."}), 400

        if not ia_validator.validar_correo_ia(nuevo_correo):
            return jsonify({
                "ok": False,
                "error": f"El correo «{nuevo_correo}» no tiene una estructura de correo electrónico válida."
            }), 400

        actualizar_config_remitente(nuevo_correo, nuevo_nombre, nueva_clave)
        tiene_clave = bool(config.SMTP_PASS and str(config.SMTP_PASS).strip())

        return jsonify({
            "ok": True,
            "smtp_from": config.SMTP_FROM,
            "smtp_from_name": config.SMTP_FROM_NAME,
            "tiene_password": tiene_clave,
            "mensaje": "Advertencia: El correo de envío ha sido modificado exitosamente. Todos los envíos futuros se realizarán desde esta nueva dirección.",
            "advertencia": "Advertencia: El correo de envío ha sido modificado exitosamente. Todos los envíos futuros se realizarán desde esta nueva dirección.",
            "mensaje_advertencia": "Advertencia: El correo de envío ha sido modificado exitosamente. Todos los envíos futuros se realizarán desde esta nueva dirección.",
            "config": {
                "smtp_from": config.SMTP_FROM,
                "smtp_from_name": config.SMTP_FROM_NAME,
                "smtp_host": config.SMTP_HOST,
                "smtp_port": config.SMTP_PORT,
                "tiene_password": tiene_clave,
                "simulacion": mail_service.envio_simulado(),
            }
        })

    return jsonify({
        "ok": True,
        "smtp_from": config.SMTP_FROM,
        "smtp_from_name": config.SMTP_FROM_NAME,
        "tiene_password": tiene_clave,
        "config": {
            "smtp_from": config.SMTP_FROM,
            "smtp_from_name": config.SMTP_FROM_NAME,
            "smtp_host": config.SMTP_HOST,
            "smtp_port": config.SMTP_PORT,
            "tiene_password": tiene_clave,
            "simulacion": mail_service.envio_simulado(),
            "configurado": mail_service.smtp_configurado(),
        }
    })


@app.route("/api/estado")
def api_estado():
    """Estado del sistema: SMTP, plantilla y estadísticas de la base de datos."""
    plantilla = config.TEMPLATES_DIR / "certificado_base.pdf"
    return jsonify(
        {
            "ok": True,
            "universidad": config.UNIVERSIDAD,
            "smtp": {
                "host": config.SMTP_HOST,
                "puerto": config.SMTP_PORT,
                "tls": config.SMTP_USE_TLS,
                "configurado": mail_service.smtp_configurado(),
                "simulacion": mail_service.envio_simulado(),
                "remitente": config.SMTP_FROM,
                "remitente_nombre": config.SMTP_FROM_NAME,
            },
            "plantilla": {"ruta": str(plantilla), "existe": plantilla.exists()},
            "base_datos": {"ruta": str(tracker.ruta_db()), "existe": tracker.ruta_db().exists()},
            "estadisticas": tracker.estadisticas(),
            "hojas_requeridas": excel_loader.HOJAS_REQUERIDAS,
        }
    )


@app.route("/api/eventos")
def api_eventos():
    """Lista los eventos procesados."""
    return jsonify({"ok": True, "eventos": tracker.listar_eventos()})


@app.route("/api/envios")
def api_envios():
    """Trazabilidad de envíos con filtros opcionales."""
    evento = request.args.get("evento")
    estado = request.args.get("estado")
    limite = int(request.args.get("limite", 200))
    return jsonify(
        {
            "ok": True,
            "envios": tracker.listar_envios(evento=evento, estado=estado, limite=limite),
            "estadisticas": tracker.estadisticas(evento),
        }
    )


@app.route("/api/plantillas")
def api_plantillas():
    """Lista las plantillas disponibles (.pdf y .pptx) en `templates/` y directorio raíz."""
    archivos = []
    # 1. Certificados.pptx en la raíz si existe
    pptx_oficial = config.BASE_DIR / "Certificados.pptx"
    if pptx_oficial.exists():
        archivos.append({
            "nombre": "certificado_base.pdf" if not (config.TEMPLATES_DIR / "certificado_base.pdf").exists() else "Certificados.pptx",
            "titulo": "Certificados.pptx (Oficial INCIETEC)",
            "archivo": "Certificados.pptx",
            "ruta": "Certificados.pptx",
            "tipo": "pptx",
            "es_oficial": True,
            "descripcion": "Plantilla oficial PowerPoint INCIETEC con diseño institucional y campos autocompletables.",
        })

    # 2. Archivos en templates/
    for p in sorted(config.TEMPLATES_DIR.glob("*")):
        if p.suffix.lower() in {".pdf", ".pptx"}:
            if p.name == "Certificados.pdf" and pptx_oficial.exists():
                continue
            tipo = "pptx" if p.suffix.lower() == ".pptx" else "pdf"
            desc = "Plantilla base de acreditación en formato PDF." if tipo == "pdf" else "Plantilla personalizada en PowerPoint."
            if p.name == "certificado_base.pdf":
                desc = "Plantilla base institucional en PDF con membrete y firmas de La Salle."
            archivos.append({
                "nombre": p.name,
                "titulo": f"{p.name} ({tipo.upper()})",
                "archivo": p.name,
                "ruta": str(p.relative_to(config.BASE_DIR)).replace("\\", "/"),
                "tipo": tipo,
                "es_oficial": p.name in {"certificado_base.pdf", "Certificados.pptx"},
                "descripcion": desc,
            })

    # Asegurar que certificado_base.pdf siempre esté presente si existe
    base_pdf = config.TEMPLATES_DIR / "certificado_base.pdf"
    if base_pdf.exists() and not any(x["nombre"] == "certificado_base.pdf" for x in archivos):
        archivos.append({
            "nombre": "certificado_base.pdf",
            "titulo": "certificado_base.pdf (PDF)",
            "archivo": "certificado_base.pdf",
            "ruta": str(base_pdf.relative_to(config.BASE_DIR)).replace("\\", "/"),
            "tipo": "pdf",
            "es_oficial": True,
            "descripcion": "Plantilla base institucional en PDF.",
        })

    return jsonify({"ok": True, "plantillas": archivos})


@app.route("/api/cargar-plantilla", methods=["POST"])
def api_cargar_plantilla():
    """Permite subir una nueva plantilla (.pptx o .pdf) para los certificados."""
    archivo = (
        request.files.get("plantilla_archivo")
        or request.files.get("archivo")
        or request.files.get("plantilla")
    )
    if not archivo or not archivo.filename:
        return jsonify({"ok": False, "error": "No se seleccionó ningún archivo de plantilla"}), 400

    nombre_seguro = secure_filename(archivo.filename)
    extension = Path(nombre_seguro).suffix.lower()
    if extension not in {".pptx", ".pdf"}:
        return jsonify({
            "ok": False,
            "error": "Formato no válido. Debe adjuntar un archivo PowerPoint (.pptx) o PDF (.pdf)."
        }), 400

    destino = config.TEMPLATES_DIR / nombre_seguro
    archivo.save(str(destino))
    LOG.info("[PDF] Nueva plantilla guardada: %s", destino.name)

    tipo = "pptx" if extension == ".pptx" else "pdf"
    ruta_relativa = str(destino.relative_to(config.BASE_DIR)).replace("\\", "/")

    return jsonify({
        "ok": True,
        "mensaje": f"Plantilla «{nombre_seguro}» cargada con éxito. Ya puedes seleccionarla para tus certificados.",
        "plantilla": {
            "nombre": nombre_seguro,
            "titulo": f"{nombre_seguro} ({tipo.upper()})",
            "archivo": nombre_seguro,
            "ruta": ruta_relativa,
            "tipo": tipo,
            "es_oficial": False,
            "descripcion": f"Plantilla personalizada ({tipo.upper()}) cargada recientemente.",
        }
    })


@app.route("/api/vista-previa-correo", methods=["GET", "POST"])
def api_vista_previa_correo():
    """Genera la vista previa de cómo se enviará el correo con la plantilla seleccionada."""
    datos = request.get_json(silent=True) or request.form or request.args
    evento = (datos.get("evento") or "Congreso de Inteligencia Artificial 2026").strip()
    destinatario = (datos.get("destinatario") or "participante@unilasallista.edu.co").strip()
    nombre = (datos.get("nombre") or "Juan Pérez González").strip()
    rol = (datos.get("rol") or "Ponente").strip()
    plantilla = (datos.get("plantilla") or "Certificados.pptx").strip()

    nombre_adjunto = f"Certificado_{secure_filename(nombre)}.pdf"
    preview = mail_service.obtener_vista_previa_correo(
        destinatario=destinatario,
        nombre=nombre,
        evento=evento,
        rol=rol,
        archivo_adjunto=nombre_adjunto,
    )
    preview["plantilla_origen"] = Path(plantilla).name
    return jsonify({"ok": True, "vista_previa": preview})


@app.route("/health")
def health():
    """Sonda de disponibilidad del servicio."""
    return jsonify({"ok": True, "servicio": "Certificado Unilasallista", "version": "1.0.0"})


@app.errorhandler(413)
def error_413(error):
    return jsonify({"ok": False, "total": 0, "error": f"Archivo mayor a {MAX_UPLOAD_MB:.0f} MB"}), 413


@app.errorhandler(500)
def error_500(error):
    return jsonify({"ok": False, "total": 0, "error": "Error interno del servidor"}), 500


# ==========================================================================
# Arranque
# ==========================================================================
if __name__ == "__main__":
    tracker.inicializar_db()
    tracker.purgar_registros(config.DIAS_RETENCION)
    puerto = int(os.getenv("PORT", 5000))
    depuracion = str(os.getenv("FLASK_DEBUG", "")).strip().lower() in {"1", "true", "yes"}
    LOG.info("Certificado Unilasallista escuchando en http://127.0.0.1:%d", puerto)
    app.run(host="0.0.0.0", port=puerto, debug=depuracion)
