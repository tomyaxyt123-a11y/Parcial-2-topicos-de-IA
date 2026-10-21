"""
Generación de certificados en PDF.

Cada certificado se compone sobre una página **A4 horizontal** con:
    - Marco institucional y logotipo de La Salle.
    - Nombre del participante centrado en verde institucional.
    - Rol, evento y aporte (ponencia / conferencia).
    - Lugar y fecha en formato "Bogotá D.C., 21 de octubre de 2026".
    - Firmas de autorización.

Si existe una plantilla base (`templates/certificado_base.pdf`) se utiliza
como fondo del certificado. Opcionalmente el PDF puede cifrarse con la
contraseña del documento del participante (protección de datos).
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

LOG = logging.getLogger("certificado")

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

COLOR_INSTITUCIONAL = colors.HexColor(os.getenv("COLOR_INSTITUCIONAL", "#007A33"))
COLOR_SECUNDARIO = colors.HexColor(os.getenv("COLOR_SECUNDARIO", "#0A3D62"))
COLOR_TEXTO = colors.HexColor("#333333")
COLOR_SUAVE = colors.HexColor("#666666")

RAIZ = Path(__file__).resolve().parent.parent
LOGO_POR_DEFECTO = RAIZ / "static" / "logo_unilasalle.png"
PLANTILLA_POR_DEFECTO = RAIZ / "templates" / "certificado_base.pdf"


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def formatear_fecha_es(fecha: Optional[object] = None, ciudad: str = "Bogotá D.C.") -> str:
    """Devuelve la fecha en formato institucional: 'Bogotá D.C., 21 de octubre de 2026'."""
    if fecha is None:
        fecha = date.today()
    elif isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha).date()
        except ValueError:
            return f"{ciudad}, {fecha}"
    elif isinstance(fecha, datetime):
        fecha = fecha.date()
    return f"{ciudad}, {fecha.day} de {MESES_ES[fecha.month - 1]} de {fecha.year}"


def comprimir_imagen(ruta: str, max_ancho: int = 900, calidad: int = 70) -> Optional[bytes]:
    """Redimensiona y comprime una imagen para incrustarla sin inflar el PDF."""
    try:
        from io import BytesIO

        from PIL import Image

        with Image.open(ruta) as imagen:
            imagen = imagen.convert("RGB")
            if imagen.width > max_ancho:
                alto = int(imagen.height * max_ancho / imagen.width)
                imagen = imagen.resize((max_ancho, alto), Image.LANCZOS)
            buffer = BytesIO()
            imagen.save(buffer, format="JPEG", quality=calidad, optimize=True)
            return buffer.getvalue()
    except Exception as exc:  # logo no disponible o corrupto
        LOG.info("No fue posible comprimir la imagen %s (%s)", ruta, exc)
        return None


# --------------------------------------------------------------------------
# Dibujo del certificado
# --------------------------------------------------------------------------
def _plantilla_disponible(plantilla: Optional[str]) -> bool:
    """Indica si la plantilla base existe y puede usarse como fondo."""
    return bool(plantilla) and Path(plantilla).exists()


def _dibujar_marco(c: canvas.Canvas, ancho: float, alto: float) -> None:
    """Marco decorativo institucional."""
    c.setStrokeColor(COLOR_INSTITUCIONAL)
    c.setLineWidth(3)
    c.rect(12 * mm, 12 * mm, ancho - 24 * mm, alto - 24 * mm)

    c.setStrokeColor(COLOR_SECUNDARIO)
    c.setLineWidth(0.8)
    c.rect(16 * mm, 16 * mm, ancho - 32 * mm, alto - 32 * mm)

    # Franja superior e inferior
    c.setFillColor(COLOR_INSTITUCIONAL)
    c.rect(16 * mm, alto - 20 * mm, ancho - 32 * mm, 2.5 * mm)
    c.setFillColor(COLOR_SECUNDARIO)
    c.rect(16 * mm, 17.5 * mm, (ancho - 32 * mm) / 3, 1.2 * mm)


def _dibujar_logotipo(c: canvas.Canvas, ancho: float, alto: float) -> None:
    """Inserta el logotipo institucional centrado en la parte superior."""
    if not Path(LOGO_POR_DEFECTO).exists():
        return
    try:
        from reportlab.lib.utils import ImageReader

        logo = ImageReader(str(LOGO_POR_DEFECTO))
        ancho_logo = 45 * mm
        c.drawImage(
            logo,
            (ancho - ancho_logo) / 2,
            alto - 16 * mm - 22 * mm,
            width=ancho_logo,
            height=20 * mm,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
    except Exception as exc:
        LOG.info("No fue posible incrustar el logotipo (%s)", exc)


def _dibujar_bloque_firmas(c: canvas.Canvas, ancho: float) -> None:
    """Líneas de firma del coordinator y del director del programa."""
    y = 32 * mm
    ancho_linea = 60 * mm
    for centro, cargo in (
        (ancho / 2 - 45 * mm, "Coordinador del evento"),
        (ancho / 2 + 45 * mm, "Director del programa"),
    ):
        c.setStrokeColor(COLOR_SUAVE)
        c.setLineWidth(0.8)
        c.line(centro - ancho_linea / 2, y, centro + ancho_linea / 2, y)
        c.setFillColor(COLOR_TEXTO)
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(centro, y - 4.5 * mm, cargo)


def _dibujar_contenido(c: canvas.Canvas, datos: Dict[str, object]) -> None:
    """Dibuja el contenido variable del certificado."""
    ancho, alto = landscape(A4)
    nombres = str(datos.get("nombres") or "").strip()
    apellidos = str(datos.get("apellidos") or "").strip()
    nombre_completo = str(datos.get("nombre_completo") or "").strip()
    if not nombre_completo:
        nombre_completo = " ".join(p for p in (nombres, apellidos) if p).strip()

    rol = str(datos.get("rol") or "Participante").strip()
    evento = str(datos.get("evento") or "").strip()
    fecha_texto = str(datos.get("fecha") or "").strip() or formatear_fecha_es(
        datos.get("fecha_texto"), str(datos.get("ciudad") or "Bogotá D.C.")
    )
    aporte = str(datos.get("ponencia") or datos.get("conferencia") or "").strip()
    institucion = str(datos.get("institucion") or "").strip()

    y = alto - 62 * mm

    c.setFillColor(COLOR_TEXTO)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(ancho / 2, y, "CERTIFICADO")
    y -= 9 * mm

    c.setFont("Helvetica", 12.5)
    c.setFillColor(COLOR_SUAVE)
    c.drawCentredString(
        ancho / 2, y,
        "La Universidad de La Salle, en cumplimiento de sus fines académicos, certifica que",
    )
    y -= 20 * mm

    # Nombre del participante en verde institucional
    c.setFillColor(COLOR_INSTITUCIONAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(ancho / 2, y, nombre_completo.upper())
    y -= 6 * mm

    c.setStrokeColor(COLOR_INSTITUCIONAL)
    c.setLineWidth(1.2)
    ancho_subrayado = min(ancho * 0.55, 220 * mm)
    c.line(ancho / 2 - ancho_subrayado / 2, y, ancho / 2 + ancho_subrayado / 2, y)
    y -= 12 * mm

    c.setFillColor(COLOR_TEXTO)
    c.setFont("Helvetica", 14)
    c.drawCentredString(ancho / 2, y, f"participó en calidad de {rol.lower()}")
    y -= 7 * mm

    if evento:
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(ancho / 2, y, evento)
        y -= 7 * mm

    if aporte:
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(COLOR_SECUNDARIO)
        etiqueta = "ponencia" if datos.get("ponencia") else "conferencia"
        c.drawCentredString(ancho / 2, y, f"con la {etiqueta} «{aporte}»")
        y -= 6 * mm

    if institucion:
        c.setFont("Helvetica", 10.5)
        c.setFillColor(COLOR_SUAVE)
        c.drawCentredString(ancho / 2, y, institucion)
        y -= 6 * mm

    # Lugar y fecha
    c.setFont("Helvetica", 10.5)
    c.setFillColor(COLOR_SUAVE)
    c.drawString(20 * mm, 24 * mm, fecha_texto)


def _fusionar_plantilla(archivo: str, plantilla: Optional[str]) -> bool:
    """Usa el PDF base como fondo del certificado generado."""
    if not plantilla:
        return False
    ruta = Path(plantilla)
    if not ruta.exists():
        LOG.info("Plantilla base no encontrada: %s (se usa el diseño por defecto)", ruta)
        return False
    try:
        from pypdf import PdfReader, PdfWriter

        lector_base = PdfReader(str(ruta))
        lector_cert = PdfReader(archivo)
        escritor = PdfWriter()
        for pagina_base in lector_base.pages:
            # `add_page` adjunta la página al escritor: el `merge_page` se
            # aplica sobre la copia, evitando el uso de páginas huérfanas.
            pagina_destino = escritor.add_page(pagina_base)
            for pagina_cert in lector_cert.pages:
                pagina_destino.merge_page(pagina_cert)

        with open(archivo, "wb") as salida:
            escritor.write(salida)
        LOG.info("Plantilla base aplicada como fondo: %s", ruta.name)
        return True
    except Exception as exc:
        LOG.info("No fue posible aplicar la plantilla base (%s)", exc)
        return False


def _cifrar_pdf(archivo: str, contrasena: str) -> bool:
    """Cifra el PDF con contraseña (protección de datos personales)."""
    if not contrasena:
        return False
    try:
        from pypdf import PdfReader, PdfWriter

        lector = PdfReader(archivo)

        def _construir(metodo_cifrado=None) -> PdfWriter:
            escritor = PdfWriter()
            for pagina in lector.pages:
                escritor.add_page(pagina)
            if metodo_cifrado:
                escritor.encrypt(contrasena, algorithm=metodo_cifrado)
            else:
                escritor.encrypt(contrasena)
            return escritor

        try:
            # AES-256 requiere el paquete opcional `cryptography`
            escritor = _construir("AES-256")
        except Exception:
            escritor = _construir()

        with open(archivo, "wb") as salida:
            escritor.write(salida)
        LOG.info("PDF protegido con contraseña (%s)", contrasena)
        return True
    except Exception as exc:
        LOG.info("No fue posible cifrar el PDF (%s)", exc)
        return False


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------
def generar_certificado(
    datos: Dict[str, object],
    plantilla: Optional[str] = None,
    salida: Optional[str] = None,
    proteger: bool = False,
    contrasena: Optional[str] = None,
) -> str:
    """Genera el certificado PDF de un participante.

    Args:
        datos: diccionario con `nombres`, `apellidos`, `rol`, `evento`,
            `fecha` y opcionalmente `ponencia`/`conferencia`, `documento`.
        plantilla: ruta del PDF base a usar como fondo (opcional).
        salida: ruta del archivo a generar; si no se indica se usa `tmp/`.
        proteger: si es `True` cifra el PDF con la contraseña del participante.
        contrasena: contraseña explícita; si no se indica se usa el documento.

    Returns:
        La ruta del archivo PDF generado.
    """
    if salida is None:
        nombre_archivo = f"{datos.get('nombres', 'certificado')}_{datos.get('apellidos', '')}".strip()
        destino = RAIZ / "tmp" / f"{nombre_archivo.replace(' ', '_')}.pdf"
    else:
        destino = Path(salida)

    destino.parent.mkdir(parents=True, exist_ok=True)

    ancho, alto = landscape(A4)
    c = canvas.Canvas(str(destino), pagesize=landscape(A4))
    c.setTitle(f"Certificado - {datos.get('nombre_completo', '')}")
    c.setAuthor("Certificado Unilasallista · Universidad de La Salle")
    c.setSubject(str(datos.get("evento", "")))

    # Si se aplica una plantilla base, el marco y el logotipo ya vienen en ella
    # y se dibujan únicamente el contenido variable.
    if _plantilla_disponible(plantilla):
        _dibujar_contenido(c, datos)
        _dibujar_bloque_firmas(c, ancho)
    else:
        _dibujar_marco(c, ancho, alto)
        _dibujar_logotipo(c, ancho, alto)
        _dibujar_contenido(c, datos)
        _dibujar_bloque_firmas(c, ancho)
    c.showPage()
    c.save()

    LOG.info("Certificado generado: %s", destino.name)

    if plantilla:
        _fusionar_plantilla(str(destino), plantilla)

    if proteger:
        clave = contrasena or str(datos.get("documento") or "").strip()
        if clave:
            _cifrar_pdf(str(destino), clave)

    return str(destino)


def generar_certificados(
    participantes: list,
    evento: str,
    plantilla: Optional[str] = None,
    directorio: Optional[str] = None,
    proteger: bool = False,
) -> list:
    """Genera un PDF por cada participante y devuelve la lista de rutas."""
    directorio = Path(directorio) if directorio else (RAIZ / "tmp")
    directorio.mkdir(parents=True, exist_ok=True)

    rutas: list = []
    for indice, participante in enumerate(participantes, start=1):
        datos = dict(participante)
        datos["evento"] = evento
        datos.setdefault("fecha", formatear_fecha_es())
        nombre = datos.get("nombre_completo") or f"participante_{indice}"
        slug = "_".join(str(nombre).title().split())
        ruta = directorio / f"{indice:04d}_{slug}.pdf"
        try:
            rutas.append(generar_certificado(datos, plantilla, str(ruta), proteger))
        except Exception as exc:
            LOG.info("[PDF] Error generando certificado para %s: %s", nombre, exc)
    return rutas
