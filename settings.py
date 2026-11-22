import json
from .db import q
def get(k, default=None):
    r = q("SELECT v FROM settings WHERE k=?", (k,)); return json.loads(r[0]["v"]) if r else default
def put(k, v): q("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, json.dumps(v)))
