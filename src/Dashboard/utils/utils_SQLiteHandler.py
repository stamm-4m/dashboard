import sqlite3
import os
from pathlib import Path
from Dashboard.config import DB_SQLITE_DIR

class SQLiteHandler:
    def __init__(self, db_folder=DB_SQLITE_DIR):
        base_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_path, "..", DB_SQLITE_DIR)
        self.db_path = db_path
        self._initialize_user_database()
        self._create_table_if_not_exists()

    def _initialize_user_database(self):
        db_path = os.path.join(self.db_path,"users.db")
        db_exists = os.path.exists(db_path)

        conn = sqlite3.connect(db_path)
        c = conn.cursor()


        if not db_exists:
            # Crear tabla si no existe
            c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
            """)
            print("✅ users.db created and users table initialized.")

        # Verificar si existe el usuario admin
        c.execute("SELECT * FROM users WHERE username = ?", ("admin",))
        if not c.fetchone():
            c.execute("""
            INSERT INTO users (username, password, role) 
            VALUES (?, ?, ?)""", ("admin", "admin123", "admin"))
            print("✅ Default user 'admin' created.")

        conn.commit()
        conn.close()

    def _create_table_if_not_exists(self):
        db_path = os.path.join(self.db_path,"point_report.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS point_report (
                    measurement TEXT,
                    prediction_var TEXT,
                    value REAL,
                    time TEXT,
                    type TEXT,
                    level TEXT,
                    PRIMARY KEY (measurement, prediction_var, time)
                )
            ''')
            conn.commit()

    def upsert_point(self, measurement, time, prediction_var, value, tags: dict):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO point_report (measurement, prediction_var, value, time, type, level)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(measurement, prediction_var, time)
                DO UPDATE SET
                    value = excluded.value,
                    type = excluded.type,
                    level = excluded.level
            ''', (
                str(measurement),
                str(prediction_var),
                float(value),
                str(time),
                tags.get("type", None),
                tags.get("level", None)
            ))
            conn.commit()
