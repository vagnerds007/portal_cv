import bcrypt
from sqlalchemy import create_engine, text

DB_URL = "sqlite:///portal.db"

engine = create_engine(DB_URL, future=True)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

username = "admin"
name = "Administrador"
password = "Caps+1234"  # TROQUE DEPOIS
role = "admin"
active = 1

with engine.begin() as con:
    # cria usuário só se não existir
    existing = con.execute(text("SELECT id FROM users WHERE username=:u"), {"u": username}).fetchone()
    if existing:
        print("Usuário admin já existe.")
    else:
        con.execute(
            text("""
                INSERT INTO users (username, name, password_hash, role, active)
                VALUES (:username, :name, :ph, :role, :active)
            """),
            {
                "username": username,
                "name": name,
                "ph": hash_pw(password),
                "role": role,
                "active": active,
            },
        )
        print("Usuário admin criado com sucesso.")
