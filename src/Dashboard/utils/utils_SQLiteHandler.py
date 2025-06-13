import sqlite3
from pathlib import Path
from Dashboard.config import DB_SQLITE_DIR

class SQLiteHandler:
    def __init__(self, db_path=DB_SQLITE_DIR):
        self.db_path = db_path
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
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
