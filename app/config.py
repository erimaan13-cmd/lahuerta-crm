"""Configuración central. Todo valor sensible llega por variables de entorno (nunca en el repo)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("CRM_DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'crm.db'}")
# Clave para firmar cookies. El valor por defecto SOLO sirve para demo local.
SECRET_KEY = os.getenv("CRM_SECRET_KEY", "dev-only-change-me")
SESSION_COOKIE = "crm_session"
SESSION_MAX_AGE_S = 8 * 3600

# Clasificador (ver DECISION_LOG D-05)
CLASSIFIER_THRESHOLD = float(os.getenv("CRM_CLASSIFIER_THRESHOLD", "0.60"))
CLASSIFIER_MIN_MARGIN = float(os.getenv("CRM_CLASSIFIER_MIN_MARGIN", "0.15"))
CLASSIFIER_ALWAYS_REVIEW = {"CALIDAD_RECLAMACION", "OTRO"}
LLM_ENABLED = os.getenv("CRM_LLM_ENABLED", "false").lower() == "true"  # P1

# Reglas de negocio (evidencia E02, E14)
MIN_ORDER_KG = 500
FIRST_CONTACT_SLA_HOURS = 4

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.com.mx", "live.com",
    "live.com.mx", "icloud.com", "prodigy.net.mx", "hotmail.es", "outlook.es", "msn.com",
}

# Dominios de proveedores conocidos (los proveedores NO son entidades del CRM; solo sirven para enrutar).
SUPPLIER_DOMAINS = {d.strip().lower() for d in os.getenv(
    "CRM_SUPPLIER_DOMAINS", "especias-origen-demo.com,importadora-demo.example").split(",") if d.strip()}

# Horario hábil (E13: L–V 8:00–17:00) y feriados adicionales de la empresa (PENDIENTE de validar)
BUSINESS_TZ = os.getenv("CRM_BUSINESS_TZ", "America/Monterrey")
BUSINESS_OPEN_HOUR = int(os.getenv("CRM_BUSINESS_OPEN_HOUR", "8"))
BUSINESS_CLOSE_HOUR = int(os.getenv("CRM_BUSINESS_CLOSE_HOUR", "17"))
EXTRA_HOLIDAYS: list = []  # p. ej. [date(2026, 12, 12)] cuando La Huerta confirme su calendario

# SLA en horas hábiles
CASE_SLA_HOURS = {"critica": 4, "alta": 8, "media": 18, "baja": 27}  # 18 h ≈ 2 días hábiles
FORMULA_TASK_HOURS = 27

# Recompra: días por defecto si la cuenta tiene un solo pedido; tolerancia sobre el intervalo promedio
REORDER_DEFAULT_DAYS = int(os.getenv("CRM_REORDER_DEFAULT_DAYS", "30"))
REORDER_TOLERANCE = float(os.getenv("CRM_REORDER_TOLERANCE", "0.2"))

# Seguridad
LOGIN_MAX_FAILS = 5
LOGIN_LOCK_MINUTES = 15
COMPANY_NAME = os.getenv("CRM_COMPANY_NAME", "EMPACADORA LA HUERTA")
