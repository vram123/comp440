
from db import get_db
from pathlib import Path

def init_db():
    import sqlite3
    schema_path = Path(__file__).parent / "schema.sql"
    with get_db() as conn, open(schema_path, "r") as f:
        conn.executescript(f.read())
        conn.commit()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
