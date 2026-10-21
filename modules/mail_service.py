"""
Servicio de envío de certificados por correo (SMTP institucional).

La configuración se lee **exclusivamente** desde variables de entorno
(`config.py` / `.env`), nunca desde el código fuente:

    SMTP_HOST=smtp.office365.com
    SMTP_PORT=587
    SMTP_USER=certificados@lasalle.edu.co
    SMTP_PASS=...
    SMTP_USE_TLS=True
    SMTP_FROM_NAME=Certificados Unilasallista

Se recomienda el SMTP institucional (Office 365) por costo cero, identidad
`@lasalle.edu.co` y cumplimiento de la política institucional de datos.
"""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Dict, List, Optional

import config

LOG = logging.getLogger("certificado")

ASUNTO = "Certificado de participación — {evento}"
PLANTILLA_CUERPO = """\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Certificado de participación</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f5;font-family:Segoe UI,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background:#f4f6f5;padding:28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:10px;overflow:hidden;
                      border-top:5px solid {COLOR_INSTITUCIONAL};
                      box-shadow:0 2px 10px rgba(0,0,0,.08);">
          <tr>
            <td style="padding:26px 34px 8px;text-align:center;">
              <h1 style="margin:0;font-size:20px;color:{COLOR_INSTITUCIONAL};
                         font-family:Segoe UI,Arial,sans-serif;">
                Certificado Unilasallista
              </h1>
              <p style="margin:6px 0 0;font-size:13px;color:#666;">
                Universidad de La Salle · {UNIVERSIDAD}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 34px 26px;color:#333;font-size:14.5px;line-height:1.6;">
              <p style="margin:0 0 14px;">Estimado(a) <strong>{NOMBRE}</strong>,</p>
              <p style="margin:0 0 14px;">
                Es un placer comunicarle que se adjunta su certificado de
                participación, correspondiente a la <strong>{ROL}</strong>
                en el evento <strong>{EVENTO}</strong>.
              </p>
              <p style="margin:0 0 14px;">
                Su certificado se genera con los datos registrados oficialmente
                por la dependencia organizadora.
              </p>
              <p style="margin:0 0 22px;">
                Agradecemos su participación y esperamos volver a contar con su
                presencia en los próximos eventos de la Universidad.
              </p>
              <p style="margin:0;color:#333;">
                Cordialmente,<br>
                <strong>{SMTP_FROM_NAME}</strong><br>
                <span style="color:#666;font-size:13px;">{UNIVERSIDAD}</span>
              </p>
            </td>
          </tr>
          <tr>
            <td style="background:#f7f9f8;color:#888;font-size:11.5px;
                       padding:14px 34px;text-align:center;">
              Este mensaje y sus datos personales son enviados con fines
              institucionales de acreditación. Tratamiento conforme a la
              Ley 1581 de 2012 (Habeas Data) y a la política de protección de
              datos de la Universidad de La Salle.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def obtener_config_smtp() -> Dict[str, object]:
    """Devuelve la configuración SMTP vigente (leída del entorno)."""
    return {
        "host": config.SMTP_HOST,
        "port": config.SMTP_PORT,
        "user": config.SMTP_USER,
        "password": config.SMTP_PASS,
        "use_tls": config.SMTP_USE_TLS,
        "use_ssl": config.SMTP_USE_SSL,
        "timeout": config.SMTP_TIMEOUT,
        "from_name": config.SMTP_FROM_NAME,
        "from": config.SMTP_FROM or config.SMTP_USER,
    }


def smtp_configurado() -> bool:
    """Indica si hay credenciales suficientes para enviar."""
    cfg = obtener_config_smtp()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def envio_simulado() -> bool:
    """Modo de demostración: genera el correo pero no lo transmite."""
    return str(os.getenv("SIMULAR_ENVIO", "")).strip().lower() in {"1", "true", "yes", "si"}


def construir_mensaje(
    destinatario: str,
    nombre: str,
    archivo_pdf: str,
    evento: str,
    rol: str = "Participante",
) -> EmailMessage:
    """Construye el mensaje MIME (HTML + PDF adjunto)."""
    cfg = obtener_config_smtp()

    mensaje = EmailMessage()
    mensaje["Subject"] = ASUNTO.format(evento=evento)
    mensaje["From"] = formataddr((cfg["from_name"], cfg["from"]))
    mensaje["To"] = destinatario
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = make_msgid(domain=str(cfg["host"]).split(".")[-1] or "lasalle.edu.co")

    cuerpo = (
        PLANTILLA_CUERPO.replace("{COLOR_INSTITUCIONAL}", config.COLOR_INSTITUCIONAL)
        .replace("{UNIVERSIDAD}", config.UNIVERSIDAD)
        .replace("{NOMBRE}", nombre or destinatario)
        .replace("{ROL}", rol)
        .replace("{EVENTO}", evento)
        .replace("{SMTP_FROM_NAME}", str(cfg["from_name"]))
    )
    mensaje.set_content(cuerpo, subtype="html")

    ruta = Path(archivo_pdf)
    if ruta.exists():
        with open(ruta, "rb") as archivo:
            mensaje.add_attachment(
                archivo.read(),
                maintype="application",
                subtype="pdf",
                filename=ruta.name,
            )
    else:
        LOG.info("[SMTP] El adjunto %s no existe; se envía sin PDF", ruta.name)

    return mensaje


def _conectar_smtp(cfg: Dict[str, object]) -> smtplib.SMTP:
    """Abre la conexión SMTP con TLS/SSL y autentica el usuario."""
    contexto = ssl.create_default_context()
    if cfg["use_ssl"]:
        servidor: smtplib.SMTP = smtplib.SMTP_SSL(
            cfg["host"], int(cfg["port"]), timeout=cfg["timeout"], context=contexto
        )
    else:
        servidor = smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=cfg["timeout"])
        if cfg["use_tls"]:
            servidor.starttls(context=contexto)
    if cfg["user"]:
        servidor.login(str(cfg["user"]), str(cfg["password"]))
    return servidor


def enviar_certificado(
    destinatario: str,
    nombre: str,
    archivo_pdf: str,
    evento: str,
    rol: str = "Participante",
    reintentos: int = 2,
    espera_reintento: float = 3.0,
    forzar_real: bool = False,
) -> Dict[str, object]:
    """Envía el certificado por correo y devuelve el resultado.

    Returns:
        ``{'estado': 'OK' | 'ERROR', 'correo': str, 'detalle': str}``
    """
    cfg = obtener_config_smtp()
    respuesta: Dict[str, object] = {
        "estado": "ERROR",
        "correo": destinatario,
        "detalle": "",
    }

    if not destinatario:
        respuesta["detalle"] = "Destinatario vacío"
        return respuesta

    simulacion_activa = envio_simulado() and not forzar_real

    if not smtp_configurado() and not simulacion_activa:
        respuesta["detalle"] = (
            "SMTP no configurado: defina SMTP_USER y SMTP_PASS en el archivo .env"
        )
        LOG.info("[SMTP] %s", respuesta["detalle"])
        return respuesta

    try:
        mensaje = construir_mensaje(destinatario, nombre, archivo_pdf, evento, rol)
    except Exception as exc:
        respuesta["detalle"] = f"Error construyendo el mensaje: {exc}"
        LOG.info("[SMTP] %s", respuesta["detalle"])
        return respuesta

    if simulacion_activa:
        respuesta["estado"] = "OK"
        respuesta["detalle"] = "Envío simulado (SIMULAR_ENVIO=True); no se transmitió el correo"
        LOG.info("[SMTP] Enviando a %s ... OK (simulado)", destinatario)
        return respuesta

    ultimo_error = ""
    for intento in range(1, max(1, reintentos) + 1):
        try:
            with _conectar_smtp(cfg) as servidor:
                servidor.send_message(mensaje)
            respuesta["estado"] = "OK"
            respuesta["detalle"] = f"Correo enviado (intento {intento})"
            LOG.info("[SMTP] Enviando a %s ... OK", destinatario)
            return respuesta
        except Exception as exc:
            ultimo_error = f"{type(exc).__name__}: {exc}"
            LOG.info("[SMTP] Error en el envío a %s (intento %d): %s", destinatario, intento, exc)
            if intento < max(1, reintentos):
                time.sleep(espera_reintento)

    respuesta["detalle"] = ultimo_error or "Error desconocido en el envío"
    return respuesta


def enviar_lote(
    participantes: List[Dict[str, object]],
    evento: str,
    generador_pdf,
    directorio: str,
    registrar,
    simular: bool = False,
) -> Dict[str, object]:
    """Procesa un lote de participantes: genera PDF, envía y registra.

    `generador_pdf` recibe (participante, ruta_pdf) y devuelve la ruta.
    `registrar` recibe (participante, estado, detalle) y persiste la traza.
    """
    resumen = {"total": 0, "ok": 0, "error": 0, "omitido": 0}
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    for indice, participante in enumerate(participantes, start=1):
        resumen["total"] += 1
        correo = str(participante.get("correo", ""))
        nombre = str(participante.get("nombre_completo", ""))

        if not correo:
            resumen["error"] += 1
            registrar(participante, "ERROR", "Correo vacío")
            continue

        ruta_pdf = generador_pdf(participante, str(directorio / f"{indice:04d}.pdf"))
        resultado = enviar_certificado(correo, nombre, ruta_pdf, evento, str(participante.get("rol", "")))
        estado = str(resultado["estado"])
        resumen["ok" if estado == "OK" else "error"] += 1
        registrar(participante, estado, str(resultado["detalle"]))

    return resumen
