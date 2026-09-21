"""Autenticación local (D-15): PBKDF2 para contraseñas y cookie firmada con HMAC."""
import base64
import hashlib
import hmac
import json
import os
import time

from app import config

_ITER = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"pbkdf2_sha256${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, it, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(it))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False


def _sign(data: bytes) -> str:
    return hmac.new(config.SECRET_KEY.encode(), data, hashlib.sha256).hexdigest()


def make_session_token(user_id: str) -> str:
    payload = json.dumps({"uid": user_id, "exp": int(time.time()) + config.SESSION_MAX_AGE_S}).encode()
    b64 = base64.urlsafe_b64encode(payload).decode()
    return f"{b64}.{_sign(b64.encode())}"


def read_session_token(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    b64, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(_sign(b64.encode()), sig):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(b64.encode()))
    except (ValueError, json.JSONDecodeError):
        return None
    if data.get("exp", 0) < time.time():
        return None
    return data.get("uid")
