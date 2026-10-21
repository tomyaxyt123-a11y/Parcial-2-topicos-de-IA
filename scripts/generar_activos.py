"""
Genera los activos del proyecto de forma reproducible:

    python scripts/generar_activos.py

Crea:
    static/logo_unilasalle.png      Logotipo institucional
    templates/certificado_base.pdf  Plantilla base del certificado
    data/ejemplo_evento.xlsx        Archivo Excel de ejemplo (5 hojas)
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

import config  # noqa: E402
from modules import excel_loader  # noqa: E402

VERDE = colors.HexColor(config.COLOR_INSTITUCIONAL)
AZUL = colors.HexColor(config.COLOR_SECUNDARIO)
GRIS = colors.HexColor("#6b7280")


# --------------------------------------------------------------------------
# Logotipo
# --------------------------------------------------------------------------
def generar_logotipo(destino: Path) -> None:
    """Crea un logotipo institucional simple (emblema circular)."""
    from PIL import Image, ImageDraw, ImageFont

    ancho = alto = 900
    imagen = Image.new("RGBA", (ancho, alto), (255, 255, 255, 0))
    dibujo = ImageDraw.Draw(imagen)

    centro = (ancho // 2, alto // 2)
    radio = 400

    # Aro exterior verde
    dibujo.ellipse(
        [centro[0] - radio, centro[1] - radio, centro[0] + radio, centro[1] + radio],
        fill=(255, 255, 255, 255),
        outline=(0, 122, 51, 255),
        width=34,
    )
    # Aro interior azul
    radio_interno = radio - 70
    dibujo.ellipse(
        [
            centro[0] - radio_interno,
            centro[1] - radio_interno,
            centro[0] + radio_interno,
            centro[1] + radio_interno,
        ],
        outline=(10, 61, 98, 255),
        width=10,
    )
    # Franja inferior
    dibujo.rectangle([120, 640, 780, 700], fill=(0, 122, 51, 255))

    def fuente(tamano: int, negrita: bool = False):
        candidatas = [
            "C:/Windows/Fonts/segoeuib.ttf" if negrita else "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if negrita
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for ruta in candidatas:
            if Path(ruta).exists():
                try:
                    return ImageFont.truetype(ruta, tamano)
                except OSError:
                    continue
        return ImageFont.load_default()

    texto1 = "UNIVERSIDAD"
    texto2 = "DE LA SALLE"
    dibujo.text((centro[0], 300), texto1, font=fuente(88, True), fill=(0, 122, 51, 255), anchor="mm")
    dibujo.text((centro[0], 410), texto2, font=fuente(88, True), fill=(10, 61, 98, 255), anchor="mm")
    dibujo.text((centro[0], 670), "BOGOTÁ D.C.", font=fuente(52), fill=(255, 255, 255, 255), anchor="mm")

    destino.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(destino)
    print(f"[OK] Logotipo generado: {destino}")


# --------------------------------------------------------------------------
# Plantilla base del certificado
# --------------------------------------------------------------------------
def generar_plantilla(destino: Path) -> None:
    """Crea el PDF base (marco + logotipo) que se usa como fondo."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    ancho, alto = landscape(A4)

    c = canvas.Canvas(str(destino), pagesize=landscape(A4))
    c.setTitle("Plantilla base - Certificado Unilasallista")

    # Marco doble
    c.setStrokeColor(VERDE)
    c.setLineWidth(3)
    c.rect(12 * mm, 12 * mm, ancho - 24 * mm, alto - 24 * mm)
    c.setStrokeColor(AZUL)
    c.setLineWidth(0.8)
    c.rect(16 * mm, 16 * mm, ancho - 32 * mm, alto - 32 * mm)

    # Franjas
    c.setFillColor(VERDE)
    c.rect(16 * mm, alto - 20 * mm, ancho - 32 * mm, 2.5 * mm)
    c.setFillColor(AZUL)
    c.rect(16 * mm, 17.5 * mm, (ancho - 32 * mm) / 3, 1.2 * mm)

    # Logotipo
    logo = RAIZ / "static" / "logo_unilasalle.png"
    if logo.exists():
        from reportlab.lib.utils import ImageReader

        c.drawImage(
            ImageReader(str(logo)),
            (ancho - 45 * mm) / 2,
            alto - 16 * mm - 22 * mm,
            width=45 * mm,
            height=20 * mm,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    # Texto institucional fijo
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(ancho / 2, 20 * mm, "Universidad de La Salle · Certificado Unilasallista")

    c.showPage()
    c.save()
    print(f"[OK] Plantilla base generada: {destino}")


# --------------------------------------------------------------------------
# Excel de ejemplo
# --------------------------------------------------------------------------
def generar_excel(destino: Path) -> None:
    """Crea el archivo Excel de ejemplo con las 5 hojas requeridas."""
    import pandas as pd

    destino.parent.mkdir(parents=True, exist_ok=True)

    asistentes = pd.DataFrame(
        {
            "nombres": [
                "juan pablo",
                "María José",
                "camila andres",
                "Andrés Felipe",
                "laura milena",
                "Julián Esteban",
                "sofia alejandra",
                "Mateo Alejandro",
            ],
            "apellidos": [
                "perezRodriguez",
                "Pérez Gómez",
                "quintero álvarez",
                "De la Torre",
                "Ramírez Castro",
                "Vargas Sánchez",
                "nieto cardona",
                "Salazar Ríos",
            ],
            "correo": [
                "juan.perez@example.com",
                "maria.gomez@example.com",
                "camila.quintero@example.com",
                "andres.torre@example.com",
                "laura.ramirez@example.com",
                "julian.vargas@example.com",
                "sofia.nieto@example.com",
                "mateo.salazar@example.com",
            ],
        }
    )

    ponentes = pd.DataFrame(
        {
            "nombres": ["ana maría", "carlos andrés", "Luisa Fernanda"],
            "apellidos": ["De La Hoz", "McCarthy", "O'Neil"],
            "correo": [
                "ana.delahoz@example.com",
                "carlos.mccarthy@example.com",
                "luisa.oneil@example.com",
            ],
            "documento": ["1023456789", "987654321", "100200300"],
            "ponencia": [
                "IA Generativa en la Educación Superior",
                "Tópicos de PLN para Análisis de Sentimientos",
                "Seguridad y Ética en Sistemas Inteligentes",
            ],
        }
    )

    conferenciantes = pd.DataFrame(
        {
            "nombres": ["diego alejandro", "paula andrea"],
            "apellidos": ["Bermúdez Ruiz", "Castillo Mejía"],
            "correo": ["diego.bermudez@example.com", "paula.castillo@example.com"],
            "documento": ["1010101010", "2020202020"],
            "conferencia": [
                "Computación Responsable y Explainable AI",
                "Datos Abiertos en la Universidad",
            ],
        }
    )

    evaluadores = pd.DataFrame(
        {
            "nombres": ["ricardo", "elena maría"],
            "apellidos": ["Hernández Cruz", "Mendoza Paz"],
            # Se usa el alias "Email" a propósito para demostrar el mapeo semántico
            "Email": ["ricardo.hernandez@example.com", "elena.mendoza@example.com"],
            "documento": ["3030303030", "4040404040"],
        }
    )

    organizadores = pd.DataFrame(
        {
            "nombres": ["maría fernanda", "jorge alejandro"],
            "apellidos": ["Ospina Vélez", "Cardona Gaviria"],
            "correo": ["maria.ospina@example.com", "jorge.cardona@example.com"],
        }
    )

    with pd.ExcelWriter(destino, engine="openpyxl") as escritor:
        asistentes.to_excel(escritor, sheet_name="Asistentes", index=False)
        ponentes.to_excel(escritor, sheet_name="Ponentes", index=False)
        conferenciantes.to_excel(escritor, sheet_name="Conferenciantes", index=False)
        evaluadores.to_excel(escritor, sheet_name="Evaluadores", index=False)
        organizadores.to_excel(escritor, sheet_name="Organizadores", index=False)

    print(f"[OK] Excel de ejemplo generado: {destino}")
    print(f"     Hojas: {', '.join(excel_loader.HOJAS_REQUERIDAS)}")


if __name__ == "__main__":
    generar_logotipo(RAIZ / "static" / "logo_unilasalle.png")
    generar_plantilla(RAIZ / "templates" / "certificado_base.pdf")
    generar_excel(RAIZ / "data" / "ejemplo_evento.xlsx")
    print("\nActivos generados correctamente.")
