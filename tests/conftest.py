"""
Configuración de las pruebas.

Define las variables de entorno **antes** de importar `config`, de modo que
las pruebas nunca toquen la base de datos real ni envíen correos reales.
"""

import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

_TMP = Path(tempfile.gettempdir()) / "certificado_unilasallista_tests"
_TMP.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DB_PATH", str(_TMP / "test_certificados.db"))
os.environ.setdefault("SIMULAR_ENVIO", "True")
os.environ.setdefault("PROTEGER_PDF", "False")
os.environ.setdefault("LIMPIAR_TEMPORALES", "False")
os.environ.setdefault("SECRET_KEY", "pruebas")
