import sqlite3
import os
base_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_path, "..", "data","users.db")
    

def get_user_by_username(username):
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para obtener los resultados como diccionarios
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username.strip(),))
    row = cursor.fetchone()
    conn.close()

    #print("🔎 Resultado de consulta:", dict(row) if row else "Usuario no encontrado")
    return dict(row) if row else None

def insert_user(username, password_hashed, role='user'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, password_hashed, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
