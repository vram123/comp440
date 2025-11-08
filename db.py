import sqlite3
from pathlib import Path
import os

DB_ENV = os.environ.get("DATABASE_PATH")
if DB_ENV:
    DB_PATH = DB_ENV
else:
    DB_PATH = Path(__file__).parent / "app.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
