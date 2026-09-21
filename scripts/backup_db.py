"""Respaldo de la base SQLite con marca de tiempo (RNF-10). Uso: python scripts/backup_db.py"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = ROOT / "data" / "crm.db"
if not src.exists():
    sys.exit("No existe data/crm.db")
dst_dir = ROOT / "backups"
dst_dir.mkdir(exist_ok=True)
dst = dst_dir / f"crm-{datetime.now():%Y%m%d-%H%M%S}.db"
with sqlite3.connect(src) as s, sqlite3.connect(dst) as d:
    s.backup(d)  # copia consistente aun con la app en uso
print(f"Respaldo creado: {dst}")
