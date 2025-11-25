import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


class SQLiteUserDB:

    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self._init_db()

    # -----------------------------
    # conexión
    # -----------------------------
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -----------------------------
    # inicializar tabla + usuarios demo
    # -----------------------------
    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                cliente_id TEXT NOT NULL
            )
        """)

        # Insertar usuarios demo si la tabla está vacía
        cur.execute("SELECT COUNT(*) AS c FROM users")
        count = cur.fetchone()["c"]

        if count == 0:
            demo_users = [
                ("admin", generate_password_hash("admin123"), "1"),
                ("ficct", generate_password_hash("ficct123"), "5"),
            ]
            cur.executemany(
                "INSERT INTO users (username, password, cliente_id) VALUES (?, ?, ?)",
                demo_users
            )
            print("Usuarios demo creados: admin/admin123 y ficct/ficct123")

        conn.commit()
        conn.close()

    # -----------------------------
    # obtener un usuario por username
    # -----------------------------
    def get_user(self, username: str):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user:
            return {
                "id": user["id"],
                "username": user["username"],
                "password": user["password"],  # hash
                "cliente_id": user["cliente_id"]
            }
        return None

    # -----------------------------
    # validar contraseña
    # -----------------------------
    def validate_password(self, hashed_password: str, plain_password: str) -> bool:
        return check_password_hash(hashed_password, plain_password)

