"""
Certificado Unilasallista
Tópicos de Inteligencia Artificial · Universidad de La Salle · 2026-II

Paquete de módulos funcionales:
    excel_loader  -> carga y validación del archivo Excel de participantes
    ia_validator  -> PLN, similitud difusa, mapeo semántico de encabezados
    pdf_generator -> generación de certificados en PDF
    mail_service  -> envío automatizado por SMTP institucional
    tracker       -> trazabilidad y auditoría en SQLite
"""

__version__ = "1.0.0"
__all__ = [
    "excel_loader",
    "ia_validator",
    "pdf_generator",
    "mail_service",
    "tracker",
]
