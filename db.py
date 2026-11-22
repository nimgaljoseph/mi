import sqlite3, threading
from .config import DB_PATH
_lock = threading.Lock()
DB = sqlite3.connect(DB_PATH, check_same_thread=False); DB.row_factory = sqlite3.Row
SCHEMA = """
CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY, level TEXT NOT NULL, content TEXT NOT NULL, tags TEXT DEFAULT '', created TEXT DEFAULT CURRENT_TIMESTAMP, updated TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS permissions(name TEXT PRIMARY KEY, mode TEXT NOT NULL DEFAULT 'ask');
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts TEXT DEFAULT CURRENT_TIMESTAMP, permission TEXT, decision TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY, ts TEXT DEFAULT CURRENT_TIMESTAMP, role TEXT, content TEXT);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, title TEXT, kind TEXT DEFAULT 'task', done INTEGER DEFAULT 0, due TEXT);
CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS docs(id INTEGER PRIMARY KEY, name TEXT, kind TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, doc_id INTEGER, text TEXT, emb BLOB);
CREATE TABLE IF NOT EXISTS faces(id INTEGER PRIMARY KEY, name TEXT, kind TEXT, vec BLOB, created TEXT DEFAULT CURRENT_TIMESTAMP);
"""
def init():
    with _lock: DB.executescript(SCHEMA); DB.commit()
def q(sql, args=()):
    with _lock:
        cur = DB.execute(sql, args); DB.commit()
        return [dict(r) for r in cur.fetchall()] if cur.description else cur.lastrowid
