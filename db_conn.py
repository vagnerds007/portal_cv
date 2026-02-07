import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")
DB_URL = f"sqlite:///{DB_PATH}"

@st.cache_resource
def engine():
    eng = create_engine(DB_URL, future=True)
    return eng

def init_db():
    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user',
      active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS dashboards (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      embed_url TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_dashboards (
      user_id INTEGER NOT NULL,
      dashboard_id INTEGER NOT NULL,
      PRIMARY KEY (user_id, dashboard_id),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
    );
    """
    with engine().begin() as con:
        # SQLite não aceita vários statements no execute direto via text,
        # então quebramos por ';'
        for stmt in [s.strip() for s in schema_sql.split(";") if s.strip()]:
            con.execute(text(stmt))

def query(sql: str, params=None) -> pd.DataFrame:
    init_db()
    with engine().connect() as con:
        res = con.execute(text(sql), params or {})
        rows = res.mappings().all()
    return pd.DataFrame(rows)

def execute(sql: str, params=None) -> int:
    init_db()
    with engine().begin() as con:
        res = con.execute(text(sql), params or {})
        return int(getattr(res, "rowcount", 0) or 0)
