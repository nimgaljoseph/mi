"""Central permission gate. Every sensitive action calls require(name)."""
from fastapi import HTTPException
from .db import q
PERMS = ["camera", "microphone", "internet", "filesystem", "browser", "screen", "apps"]
# mode: ask (default) | always | deny | once (single-use grant, consumed on use)
def get(name):
    assert name in PERMS, f"unknown permission {name}"
    r = q("SELECT mode FROM permissions WHERE name=?", (name,))
    return r[0]["mode"] if r else "ask"
def set_mode(name, mode, detail=""):
    assert name in PERMS and mode in ("ask", "always", "deny", "once")
    q("INSERT INTO permissions(name,mode) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET mode=excluded.mode", (name, mode))
    q("INSERT INTO audit(permission,decision,detail) VALUES(?,?,?)", (name, mode, detail))
def decide(name, decision, detail=""):
    mode = {"allow_once": "once", "always_allow": "always", "deny": "deny"}[decision]
    set_mode(name, mode, detail)
def require(name, detail=""):
    m = get(name)
    if m == "always": return True
    if m == "once":
        q("UPDATE permissions SET mode='ask' WHERE name=?", (name,))
        q("INSERT INTO audit(permission,decision,detail) VALUES(?,?,?)", (name, "used-once", detail)); return True
    raise HTTPException(403, {"permission_required": name, "state": m, "detail": detail})
def all_states(): return {p: get(p) for p in PERMS}
def active(name, detail=""):
    """Non-consuming check for session permissions (camera, microphone): allowed while mode is once/always."""
    if get(name) in ("always", "once"): return True
    raise HTTPException(403, {"permission_required": name, "state": get(name), "detail": detail})
