import hashlib
import os
from datetime import datetime


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        parts = stored_hash.split(":")
        if len(parts) != 2:
            return False
        salt, hashed = parts
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except Exception:
        return False


def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} daqiqa"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours} soat"
    return f"{hours} soat {mins} daqiqa"


def format_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%H:%M | %d-%m-%Y")
