"""
Casos de prueba del flujo completo (informe de pruebas del README).

Se cubren los 10 casos definidos en la sección 7.1:

    1. Carga de un Excel válido          6.  Encabezado "Email" -> "correo"
    2. Excel sin hojas requeridas        7.  Generación del PDF
    3. Normalización de nombres (PLN)    8.  Envío SMTP exitoso
    4. Correo inválido                   9.  Envío fallido
    5. Detección de duplicados          10.  Reenvío duplicado (omitido)
"""

from __future__ import annotations

import socket
import threading
from pathlib import Path

import pandas as pd
import pytest

import config
from modules import excel_loader, ia_validator, mail_service, pdf_generator, tracker

RAIZ = Path(__file__).resolve().parent.parent
EXCEL_EJEMPLO = RAIZ / "data" / "ejemplo_evento.xlsx"
PLANTILLA = RAIZ / "templates" / "certificado_base.pdf"


# ==========================================================================
# Utilidades de prueba
# ==========================================================================
class ServidorSMTPPrueba:
    """Servidor SMTP mínimo para probar envíos reales contra localhost."""

    def __init__(self, rechazar_destinatario: bool = False):
        self.rechazar_destinatario = rechazar_destinatario
        self.mensajes: list = []
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(5)
        self._socket.settimeout(0.5)
        self.puerto = self._socket.getsockname()[1]
        self._activo = True
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def _bucle(self) -> None:
        while self._activo:
            try:
                conexion, _ = self._socket.accept()
            except (socket.timeout, OSError):
                continue
            threading.Thread(target=self._atender, args=(conexion,), daemon=True).start()

    def _atender(self, conexion: socket.socket) -> None:
        archivo = conexion.makefile("rwb")
        cuerpo = []
        en_datos = False
        try:
            archivo.write(b"220 localhost ESMTP Prueba\r\n")
            archivo.flush()
            for linea in archivo:
                texto = linea.decode("utf-8", "ignore").strip()
                if en_datos:
                    if texto == ".":
                        en_datos = False
                        self.mensajes.append(b"\n".join(cuerpo).decode("utf-8", "ignore"))
                        cuerpo = []
                        archivo.write(b"250 2.0.0 OK: queued\r\n")
                    else:
                        cuerpo.append(linea)
                    archivo.flush()
                    continue

                comando = texto.split(" ")[0].upper()
                if comando == "EHLO":
                    archivo.write(b"250-localhost\r\n250-AUTH PLAIN LOGIN\r\n250 8BITMIME\r\n")
                elif comando == "HELO":
                    archivo.write(b"250 localhost\r\n")
                elif comando == "AUTH":
                    archivo.write(b"235 2.7.0 Authentication successful\r\n")
                elif comando == "MAIL":
                    archivo.write(b"250 2.1.0 OK\r\n")
                elif comando == "RCPT":
                    if self.rechazar_destinatario:
                        archivo.write(b"550 5.1.1 Recipient rejected\r\n")
                    else:
                        archivo.write(b"250 2.1.5 OK\r\n")
                elif comando == "DATA":
                    en_datos = True
                    archivo.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                elif comando == "QUIT":
                    archivo.write(b"221 2.0.0 Bye\r\n")
                    archivo.flush()
                    break
                else:
                    archivo.write(b"250 2.0.0 OK\r\n")
                archivo.flush()
        except OSError:
            pass
        finally:
            try:
                archivo.close()
                conexion.close()
            except OSError:
                pass

    def cerrar(self) -> None:
        self._activo = False
        try:
            self._socket.close()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def _base_de_datos_limpia(tmp_path, monkeypatch):
    """Cada prueba usa una base de datos SQLite aislada."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "prueba.db")
    tracker.inicializar_db()
    yield


@pytest.fixture
def excel_valido(tmp_path) -> Path:
    """Excel con las 5 hojas requeridas."""
    ruta = tmp_path / "evento.xlsx"
    with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
        pd.DataFrame(
            {"nombres": ["juan pablo"], "apellidos": ["perez"], "correo": ["juan@example.com"]}
        ).to_excel(escritor, sheet_name="Asistentes", index=False)
        pd.DataFrame(
            {
                "nombres": ["ana"],
                "apellidos": ["lopez"],
                "correo": ["ana@example.com"],
                "documento": ["123456"],
                "ponencia": ["IA aplicada"],
            }
        ).to_excel(escritor, sheet_name="Ponentes", index=False)
        pd.DataFrame(
            {
                "nombres": ["luis"],
                "apellidos": ["gomez"],
                "correo": ["luis@example.com"],
                "documento": ["654321"],
                "conferencia": ["Charla inaugural"],
            }
        ).to_excel(escritor, sheet_name="Conferenciantes", index=False)
        pd.DataFrame(
            {
                "nombres": ["maria"],
                "apellidos": ["rios"],
                "correo": ["maria@example.com"],
                "documento": ["111222"],
            }
        ).to_excel(escritor, sheet_name="Evaluadores", index=False)
        pd.DataFrame(
            {"nombres": ["carlos"], "apellidos": ["diaz"], "correo": ["carlos@example.com"]}
        ).to_excel(escritor, sheet_name="Organizadores", index=False)
    return ruta


# ==========================================================================
# Caso 1 - Carga de un Excel válido
# ==========================================================================
def test_caso_01_carga_excel_valido(excel_valido):
    """Caso 1: un archivo con las 5 hojas se carga correctamente."""
    datos = excel_loader.cargar_excel(str(excel_valido))
    assert len(datos) == 5
    assert set(datos.keys()) == set(excel_loader.HOJAS_REQUERIDAS)
    assert excel_loader.validar_campos(datos) == []


# ==========================================================================
# Caso 2 - Excel sin las hojas requeridas
# ==========================================================================
def test_caso_02_excel_sin_hojas(tmp_path):
    """Caso 2: un Excel incompleto produce un error descriptivo."""
    ruta = tmp_path / "incompleto.xlsx"
    with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
        pd.DataFrame({"nombres": ["x"], "correo": ["x@example.com"]}).to_excel(
            escritor, sheet_name="Asistentes", index=False
        )

    with pytest.raises(excel_loader.ExcelInvalidoError) as error:
        excel_loader.cargar_excel(str(ruta))

    mensaje = str(error.value)
    assert "Faltan hojas requeridas" in mensaje
    assert "Ponentes" in mensaje


def test_caso_02b_archivo_inexistente():
    with pytest.raises(excel_loader.ExcelInvalidoError):
        excel_loader.cargar_excel("archivo/que/no/existe.xlsx")


# ==========================================================================
# Caso 3 - Normalización de nombres con PLN
# ==========================================================================
def test_caso_03_normalizacion_nombres():
    """Caso 3: 'María José Pérez' se normaliza a 'Maria Jose Perez'."""
    assert ia_validator.normalizar_nombre("María José Pérez") == "Maria Jose Perez"
    assert ia_validator.normalizar_nombre("juan  perez ") == "Juan Perez"
    assert ia_validator.normalizar_nombre("  maría   jose  ") == "Maria Jose"
    assert ia_validator.normalizar_nombre("ana de la torres") == "Ana de la Torres"
    assert ia_validator.normalizar_nombre("carlos mc donald") == "Carlos Mc Donald"
    assert ia_validator.normalizar_nombre("McCarthy") == "McCarthy"
    assert ia_validator.normalizar_nombre("O'Neil") == "O'Neil"
    assert ia_validator.normalizar_nombre("perezRodriguez") == "Perez Rodriguez"
    assert ia_validator.normalizar_nombre("PEREZ") == "Perez"
    assert ia_validator.normalizar_nombre(None) == ""
    assert ia_validator.normalizar_nombre(float("nan")) == ""


def test_caso_03b_normalizacion_en_el_excel(excel_valido):
    """El flujo completo aplica la normalización a los participantes."""
    datos = excel_loader.cargar_excel(str(excel_valido))
    participantes = excel_loader.extraer_participantes(datos)
    por_rol = {p["rol"]: p for p in participantes}
    assert por_rol["Asistentes"]["nombre_completo"] == "Juan Pablo Perez"


# ==========================================================================
# Caso 4 - Correo inválido
# ==========================================================================
def test_caso_04_correo_invalido():
    """Caso 4: 'juan@sinDominio' es rechazado."""
    assert ia_validator.validar_correo_ia("juan@sinDominio") is False
    assert ia_validator.validar_correo_ia("juan.perez@example.com") is True
    assert ia_validator.validar_correo_ia("") is False
    assert ia_validator.validar_correo_ia(None) is False


def test_caso_04b_anomalias_detectadas():
    """El detector de anomalías reporta correo inválido y documento atípico."""
    anomalias = ia_validator.detectar_anomalias(
        {"nombres": "Juan", "apellidos": "Pérez", "correo": "juan@sinDominio", "documento": "1"}
    )
    assert any("Correo inválido" in a for a in anomalias)
    assert any("Documento" in a for a in anomalias)


# ==========================================================================
# Caso 5 - Detección de duplicados por similitud difusa
# ==========================================================================
def test_caso_05_duplicados_detectados():
    """Caso 5: dos correos al 95 % de similitud se reportan como duplicados."""
    df = pd.DataFrame(
        {
            "correo": [
                "juan.perez@example.com",
                "juan.perez@example.co",
                "otra.persona@example.com",
            ]
        }
    )
    duplicados = ia_validator.detectar_duplicados(df, umbral=90)
    assert len(duplicados) == 1
    indice_a, indice_b, puntaje = duplicados[0]
    assert (indice_a, indice_b) == (0, 1)
    assert puntaje >= 90


def test_caso_05b_duplicados_por_nombre():
    df = pd.DataFrame(
        {"nombres": ["ana maría", "ana maria"], "apellidos": ["lopez", "lopez"]}
    )
    duplicados = ia_validator.detectar_duplicados_por_nombre(df, umbral=90)
    assert len(duplicados) == 1


# ==========================================================================
# Caso 6 - Mapeo semántico de encabezados
# ==========================================================================
def test_caso_06_encabezado_email():
    """Caso 6: la columna 'Email' se mapea al campo canónico 'correo'."""
    mapeo = ia_validator.mapear_encabezados(["Nombres", "Apellidos", "Email", "Documento"])
    assert mapeo["Email"] == "correo"
    assert mapeo["Nombres"] == "nombres"
    assert mapeo["Apellidos"] == "apellidos"
    assert mapeo["Documento"] == "documento"


def test_caso_06b_encabezado_parecido():
    """Un encabezado casi idéntico también se reconoce por similitud."""
    mapeo = ia_validator.mapear_encabezados(["Correo electronico", "Nombres completos"], umbral=80)
    assert mapeo["Correo electronico"] == "correo"


def test_caso_06c_encabezado_en_el_excel(tmp_path):
    """La validación de campos acepta el alias 'Email'."""
    ruta = tmp_path / "alias.xlsx"
    with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
        pd.DataFrame(
            {"nombres": ["x"], "apellidos": ["y"], "Email": ["x@example.com"]}
        ).to_excel(escritor, sheet_name="Asistentes", index=False)
        for hoja in excel_loader.HOJAS_REQUERIDAS[1:]:
            pd.DataFrame(
                {
                    "nombres": ["x"],
                    "apellidos": ["y"],
                    "correo": ["x@example.com"],
                    "documento": ["1"],
                    "ponencia": ["p"],
                    "conferencia": ["c"],
                }
            ).to_excel(escritor, sheet_name=hoja, index=False)

    datos = excel_loader.cargar_excel(str(ruta))
    assert excel_loader.validar_campos(datos) == []

    datos_mapeados, reporte = excel_loader.mapear_encabezados_hojas(datos)
    assert "correo" in datos_mapeados["Asistentes"].columns
    assert any(r["columna_original"] == "Email" for r in reporte)


# ==========================================================================
# Caso 7 - Generación del PDF
# ==========================================================================
def test_caso_07_generacion_pdf(tmp_path):
    """Caso 7: se genera un PDF A4 horizontal con los datos del participante."""
    salida = tmp_path / "certificado.pdf"
    datos = {
        "nombres": "Juan Pablo",
        "apellidos": "Perez",
        "nombre_completo": "Juan Pablo Perez",
        "rol": "Ponente",
        "evento": "Congreso de IA 2026",
        "ponencia": "IA Generativa en la Educación",
        "fecha": "Bogotá D.C., 21 de octubre de 2026",
    }
    ruta = pdf_generator.generar_certificado(datos, None, str(salida))

    assert Path(ruta).exists()
    assert Path(ruta).stat().st_size > 1000
    with open(ruta, "rb") as archivo:
        assert archivo.read(5) == b"%PDF-"


def test_caso_07b_generacion_con_plantilla(tmp_path):
    """El certificado puede generarse sobre la plantilla base."""
    salida = tmp_path / "certificado_con_plantilla.pdf"
    datos = {
        "nombres": "Ana",
        "apellidos": "Lopez",
        "nombre_completo": "Ana Lopez",
        "rol": "Asistente",
        "evento": "Congreso de IA 2026",
    }
    ruta = pdf_generator.generar_certificado(datos, str(PLANTILLA), str(salida))
    assert Path(ruta).exists()
    assert Path(ruta).stat().st_size > 1000


def test_caso_07c_pdf_protegido(tmp_path):
    """El PDF puede cifrarse con el número de documento (protección de datos)."""
    salida = tmp_path / "certificado_protegido.pdf"
    datos = {
        "nombres": "Ana",
        "apellidos": "Lopez",
        "nombre_completo": "Ana Lopez",
        "rol": "Ponente",
        "evento": "Congreso de IA 2026",
        "documento": "1023456789",
    }
    ruta = pdf_generator.generar_certificado(datos, None, str(salida), proteger=True)
    assert Path(ruta).exists()

    from pypdf import PdfReader

    lector = PdfReader(ruta)
    assert lector.is_encrypted


# ==========================================================================
# Caso 8 - Envío SMTP exitoso
# ==========================================================================
def test_caso_08_envio_smtp_exitoso(tmp_path, monkeypatch):
    """Caso 8: el correo se envía y el servidor SMTP lo recibe."""
    servidor = ServidorSMTPPrueba()
    monkeypatch.setattr(mail_service, "envio_simulado", lambda: False)
    monkeypatch.setattr(config, "SMTP_HOST", "127.0.0.1")
    monkeypatch.setattr(config, "SMTP_PORT", servidor.puerto)
    monkeypatch.setattr(config, "SMTP_USER", "prueba@lasalle.edu.co")
    monkeypatch.setattr(config, "SMTP_PASS", "clave-de-prueba")
    monkeypatch.setattr(config, "SMTP_USE_TLS", False)
    monkeypatch.setattr(config, "SMTP_USE_SSL", False)
    monkeypatch.setattr(config, "SMTP_FROM", "prueba@lasalle.edu.co")

    pdf = tmp_path / "certificado.pdf"
    pdf_generator.generar_certificado(
        {"nombres": "Ana", "apellidos": "Lopez", "nombre_completo": "Ana Lopez",
         "rol": "Asistente", "evento": "Congreso de IA 2026"},
        None,
        str(pdf),
    )

    resultado = mail_service.enviar_certificado(
        "destinatario@example.com", "Ana Lopez", str(pdf), "Congreso de IA 2026", "Asistente"
    )
    servidor.cerrar()

    assert resultado["estado"] == "OK"
    assert resultado["correo"] == "destinatario@example.com"
    assert len(servidor.mensajes) == 1
    assert "Congreso de IA 2026" in servidor.mensajes[0]


# ==========================================================================
# Caso 9 - Envío fallido
# ==========================================================================
def test_caso_09_envio_fallido(tmp_path, monkeypatch):
    """Caso 9: si el servidor rechaza el destinatario se registra ERROR."""
    servidor = ServidorSMTPPrueba(rechazar_destinatario=True)
    monkeypatch.setattr(mail_service, "envio_simulado", lambda: False)
    monkeypatch.setattr(config, "SMTP_HOST", "127.0.0.1")
    monkeypatch.setattr(config, "SMTP_PORT", servidor.puerto)
    monkeypatch.setattr(config, "SMTP_USER", "prueba@lasalle.edu.co")
    monkeypatch.setattr(config, "SMTP_PASS", "clave-de-prueba")
    monkeypatch.setattr(config, "SMTP_USE_TLS", False)
    monkeypatch.setattr(config, "SMTP_USE_SSL", False)
    monkeypatch.setattr(config, "SMTP_FROM", "prueba@lasalle.edu.co")

    resultado = mail_service.enviar_certificado(
        "rechazado@example.com", "Ana Lopez", str(tmp_path / "x.pdf"), "Evento"
    )
    servidor.cerrar()

    assert resultado["estado"] == "ERROR"
    assert resultado["detalle"]


# ==========================================================================
# Caso 10 - Reenvío duplicado (omitido)
# ==========================================================================
def test_caso_10_reenvio_duplicado_omitido():
    """Caso 10: el mismo evento + correo no se vuelve a enviar."""
    tracker.registrar_envio("Evento X", "Asistentes", "Ana Lopez", "ana@example.com", "OK", "Enviado")
    assert tracker.ya_enviado("Evento X", "ana@example.com") is True
    assert tracker.ya_enviado("Evento X", "otro@example.com") is False
    assert tracker.ya_enviado("Otro Evento", "ana@example.com") is False


# ==========================================================================
# Flujo completo (API HTTP)
# ==========================================================================
def test_flujo_completo_api(excel_valido):
    """El endpoint /procesar ejecuta el flujo completo y registra la trazabilidad."""
    import app as modulo_app

    cliente = modulo_app.app.test_client()
    with open(excel_valido, "rb") as archivo:
        respuesta = cliente.post(
            "/procesar",
            data={
                "evento": "Congreso de Prueba",
                "dependencia": "Facultad de Ingeniería",
                "excel": (archivo, "evento.xlsx"),
            },
            content_type="multipart/form-data",
        )

    cuerpo = respuesta.get_json()
    assert respuesta.status_code == 200
    assert cuerpo["ok"] is True
    assert cuerpo["total"] == 5
    assert cuerpo["detalle"]["roles"]["ok"] == 5
    assert cuerpo["detalle"]["roles"]["error"] == 0

    # Segunda ejecución: todos los participantes se vuelven a procesar y generar sí o sí
    with open(excel_valido, "rb") as archivo:
        segunda = cliente.post(
            "/procesar",
            data={
                "evento": "Congreso de Prueba",
                "excel": (archivo, "evento.xlsx"),
            },
            content_type="multipart/form-data",
        )

    cuerpo_segundo = segunda.get_json()
    assert cuerpo_segundo["ok"] is True
    assert cuerpo_segundo["detalle"]["roles"]["ok"] == 5
    assert cuerpo_segundo["detalle"]["roles"]["error"] == 0


def test_api_estado_y_trazabilidad():
    import app as modulo_app

    cliente = modulo_app.app.test_client()
    estado = cliente.get("/api/estado").get_json()
    assert estado["ok"] is True
    assert "host" in estado["smtp"] and "puerto" in estado["smtp"]
    assert estado["smtp"]["host"] == config.SMTP_HOST
    assert len(estado["hojas_requeridas"]) == 5

    envios = cliente.get("/api/envios").get_json()
    assert envios["ok"] is True
    assert "estadisticas" in envios

    salud = cliente.get("/health").get_json()
    assert salud["ok"] is True


def test_api_plantillas():
    import app as modulo_app

    cliente = modulo_app.app.test_client()
    respuesta = cliente.get("/api/plantillas").get_json()
    assert respuesta["ok"] is True
    assert any(p["nombre"] == "certificado_base.pdf" for p in respuesta["plantillas"])


# ==========================================================================
# Excel de ejemplo incluido en el repositorio
# ==========================================================================
def test_excel_de_ejemplo_es_valido():
    """El archivo `data/ejemplo_evento.xlsx` cumple el formato requerido."""
    assert EXCEL_EJEMPLO.exists(), "Ejecute: python scripts/generar_activos.py"
    datos = excel_loader.cargar_excel(str(EXCEL_EJEMPLO))
    assert excel_loader.validar_campos(datos) == []

    participantes = excel_loader.extraer_participantes(datos)
    assert len(participantes) >= 15
    # Todos los correos del ejemplo son válidos
    for participante in participantes:
        assert ia_validator.validar_correo_ia(participante["correo"])


def test_api_configuracion_correo():
    """Valida lectura y actualización dinámica del remitente SMTP con advertencia de seguridad."""
    import app as modulo_app

    cliente = modulo_app.app.test_client()
    
    # 1. Consulta GET inicial
    res_get = cliente.get("/api/configuracion-correo").get_json()
    assert res_get["ok"] is True
    assert "smtp_from" in res_get

    # 2. Actualización POST exitosa con nueva contraseña
    nuevo_correo = "certificados.prueba@unilasallista.edu.co"
    nuevo_nombre = "Unilasallista Oficial"
    nueva_clave = "ClaveSecreta123!"
    res_post = cliente.post(
        "/api/configuracion-correo",
        json={"correo": nuevo_correo, "nombre": nuevo_nombre, "password": nueva_clave},
    ).get_json()

    assert res_post["ok"] is True
    assert res_post["smtp_from"] == nuevo_correo
    assert res_post["smtp_from_name"] == nuevo_nombre
    assert res_post["tiene_password"] is True
    assert "Advertencia: El correo de envío ha sido modificado exitosamente." in res_post["mensaje_advertencia"]
    assert "Todos los envíos futuros se realizarán desde esta nueva dirección." in res_post["mensaje_advertencia"]

    # 3. Validación de correo inválido
    res_invalido = cliente.post(
        "/api/configuracion-correo",
        json={"correo": "correo-invalido-sin-arroba", "nombre": "Test"},
    )
    assert res_invalido.status_code == 400
    assert res_invalido.get_json()["ok"] is False

