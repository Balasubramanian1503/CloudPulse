import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).with_name("cloudpulse.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY AUTOINCREMENT, incident_type TEXT NOT NULL, message TEXT NOT NULL, severity TEXT NOT NULL, created_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS metric_history (id INTEGER PRIMARY KEY AUTOINCREMENT, cpu REAL, memory REAL, server_status TEXT, recorded_at TEXT NOT NULL)""")

def create_user(name,email,password_hash):
    with connect() as conn:
        conn.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",(name,email,password_hash,datetime.now(timezone.utc).isoformat()))

def get_user(email):
    with connect() as conn:
        row=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        return dict(row) if row else None

def add_incident(incident_type,message,severity):
    with connect() as conn:
        conn.execute("INSERT INTO incidents(incident_type,message,severity,created_at) VALUES(?,?,?,?)",(incident_type,message,severity,datetime.now(timezone.utc).isoformat()))

def get_incidents(limit=50):
    with connect() as conn:
        rows=conn.execute("SELECT id,incident_type,message,severity,created_at FROM incidents ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) for r in rows]

def save_metric(cpu,memory,status):
    with connect() as conn:
        conn.execute("INSERT INTO metric_history(cpu,memory,server_status,recorded_at) VALUES(?,?,?,?)",(cpu,memory,status,datetime.now(timezone.utc).isoformat()))

def get_history(limit=30):
    with connect() as conn:
        rows=conn.execute("SELECT cpu,memory,server_status,recorded_at FROM metric_history ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]


def has_recent_high_cpu(minutes=10):
    from datetime import timedelta
    cutoff=(datetime.now(timezone.utc)-timedelta(minutes=minutes)).isoformat()
    with connect() as conn:
        row=conn.execute("SELECT id FROM incidents WHERE incident_type='HIGH_CPU' AND created_at>=? ORDER BY id DESC LIMIT 1",(cutoff,)).fetchone()
        return row is not None
