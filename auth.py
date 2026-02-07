import bcrypt
from db_conn import query

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def login(username: str, password: str):
    rows = query(
        "SELECT id, username, name, password_hash, role, active "
        "FROM users WHERE username=:u",
        {"u": username},
    )
    if rows.empty:
        return None
    r = rows.iloc[0]
    if int(r["active"]) != 1:
        return None
    if not verify_password(password, r["password_hash"]):
        return None
    return {"id": int(r["id"]), "username": r["username"], "name": r["name"], "role": r["role"]}
