# ==========================================================================
# Certificado Unilasallista - Configuracion general
# Tópicos de Inteligencia Artificial · Universidad de La Salle · 2026-II
# ==========================================================================
"""Configuración central del proyecto.

Las credenciales SMTP NUNCA se escriben en el código: se leen del archivo
`.env` (o de variables de entorno del sistema / gestor de secretos).
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carga de `.env` (si existe) -> variables de entorno
load_dotenv(BASE_DIR / ".env")


def _bool(nombre: str, defecto: bool = False) -> bool:
    """Lee una variable booleana desde el entorno."""
    valor = os.getenv(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "t", "yes", "y", "si", "sí"}


def _int(nombre: str, defecto: int) -> int:
    try:
        return int(os.getenv(nombre, defecto))
    except (TypeError, ValueError):
        return defecto


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
TMP_DIR = BASE_DIR / "tmp"
OUT_DIR = BASE_DIR / "out"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
INSTANCE_DIR = BASE_DIR / "instance"

for _directorio in (TMP_DIR, OUT_DIR, DATA_DIR, INSTANCE_DIR):
    _directorio.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Base de datos (trazabilidad)
# --------------------------------------------------------------------------
DB_PATH = Path(os.getenv("DB_PATH", str(INSTANCE_DIR / "certificados.db")))

# --------------------------------------------------------------------------
# Servidor de correo (SMTP institucional)
# --------------------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = _int("SMTP_PORT", 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_USE_TLS = _bool("SMTP_USE_TLS", True)
SMTP_USE_SSL = _bool("SMTP_USE_SSL", False)
SMTP_TIMEOUT = _int("SMTP_TIMEOUT", 30)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Certificados Unilasallista")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

# --------------------------------------------------------------------------
# Comportamiento del flujo
# --------------------------------------------------------------------------
UMBRAL_SIMILITUD = _int("UMBRAL_SIMILITUD", 90)       # % para duplicados
UMBRAL_ENCABEZADO = _int("UMBRAL_ENCABEZADO", 85)     # % para mapear columnas
PROTEGER_PDF = _bool("PROTEGER_PDF", True)            # cifrar PDF con contraseña
PDF_PASSWORD = os.getenv("PDF_PASSWORD", "")          # contraseña por defecto (sin documento)
LIMPIAR_TEMPORALES = _bool("LIMPIAR_TEMPORALES", True)
MAX_CONTENT_LENGTH = _int("MAX_CONTENT_LENGTH", 32 * 1024 * 1024)  # 32 MB
DIAS_RETENCION = _int("DIAS_RETENCION", 30)           # purga de trazabilidad antigua

# --------------------------------------------------------------------------
# Identidad institucional
# --------------------------------------------------------------------------
UNIVERSIDAD = os.getenv("UNIVERSIDAD", "Corporación Universitaria Unilasallista")
PROGRAMA = os.getenv("PROGRAMA", "Tópicos de Inteligencia Artificial")
COLOR_INSTITUCIONAL = os.getenv("COLOR_INSTITUCIONAL", "#007A33")
COLOR_SECUNDARIO = os.getenv("COLOR_SECUNDARIO", "#0B1037")
CIUDAD = os.getenv("CIUDAD", "Caldas, Antioquia")


# --------------------------------------------------------------------------
# Logging con los prefijos usados en la evidencia de ejecución
# --------------------------------------------------------------------------
class _PrefijoFormatter(logging.Formatter):
    """Formatea cada registro con una etiqueta funcional: [INFO], [IA], ..."""

    ETIQUETAS = {
        "INFO": "INFO",
        "IA": "IA",
        "PDF": "PDF",
        "SMTP": "SMTP",
        "DB": "DB",
        "ERROR": "ERROR",
        "WARNING": "WARNING",
    }

    def format(self, record: logging.LogRecord) -> str:
        etiqueta = self.ETIQUETAS.get(record.levelname, record.levelname)
        mensaje = super().format(record)
        return f"[{etiqueta}] {mensaje}"


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """Configura el logger raíz con el formato `[ETIQUETA] mensaje`."""
    logger = logging.getLogger("certificado")
    if logger.handlers:
        return logger
    logger.setLevel(nivel)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_PrefijoFormatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


LOG = configurar_logging()


class Config:
    """Objeto de configuración para Flask."""

    BASE_DIR = BASE_DIR
    TMP_DIR = TMP_DIR
    OUT_DIR = OUT_DIR
    DATA_DIR = DATA_DIR
    STATIC_DIR = STATIC_DIR
    TEMPLATES_DIR = TEMPLATES_DIR
    INSTANCE_DIR = INSTANCE_DIR
    DB_PATH = DB_PATH
    SECRET_KEY = os.getenv("SECRET_KEY", "unilasallista-cambio-en-produccion")
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    JSON_AS_ASCII = False
