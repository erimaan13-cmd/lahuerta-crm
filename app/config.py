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
