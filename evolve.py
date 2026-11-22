"""Self-improvement using the LOCAL model only. Everything it changes is logged and undoable."""
import json, re, time
from . import memory, llm, settings, db
def _j(t):
    try: return json.loads(re.search(r"\{[\s\S]*\}", t).group(0))
    except Exception: return None
def _norm(s): return re.sub(r"[^a-z0-9 ]", "", str(s).lower()).strip()
def log(text):
    l = settings.get("log", []); l.insert(0, {"ts": int(time.time()), "text": text}); settings.put("log", l[:40])
def _recent(n=8): return "\n".join(f"{r['role']}: {r['content']}" for r in db.q("SELECT role,content FROM conversations ORDER BY id DESC LIMIT ?", (n,))[::-1])
async def autolearn(owner):
    known = "\n".join("- " + m["content"][:200] for m in memory.search("", limit=25)) or "nothing"
    o = _j(await llm.generate(f"From this conversation extract only durable useful facts {owner} stated about themselves (preferences, goals, projects, skills, routines, communication style). Skip sensitive data (health, money, passwords, IDs) and anything already known. Reply ONLY JSON: {{\"facts\":[\"short fact\"],\"goals\":[\"goal\"]}} with empty arrays if nothing.\n\nAlready known:\n{known}\n\nConversation:\n{_recent()}", True))
    if not o: return 0
    n = 0
    for f in (o.get("facts") or [])[:4]:
        f = str(f).strip()
        if f and not any(_norm(f) in _norm(m["content"]) or _norm(m["content"]) in _norm(f) for m in memory.search("", limit=200)):
            memory.add("long_term", f, "auto"); n += 1
    for g in (o.get("goals") or [])[:2]:
        if g and not db.q("SELECT 1 FROM tasks WHERE title=?", (str(g),)): db.q("INSERT INTO tasks(title,kind) VALUES(?, 'goal')", (str(g),)); n += 1
    if n: log(f"Learned {n} new thing(s) from our conversation")
    return n
async def reflect(owner):
    mems = memory.search("", limit=200)
    listing = "\n".join(f"{m['id']}: {m['content'][:300]}" for m in mems) or "none"
    o = _j(await llm.generate(f"You are Mini's self-improvement process. Review what Mini knows about {owner}.\nMemories (id: text):\n{listing}\n\nProfile now: {settings.get('profile','none')}\n\nRecent conversation:\n{_recent()}\n\nReply ONLY JSON: {{\"merges\":[{{\"ids\":[1,2],\"text\":\"merged memory\"}}],\"profile\":\"under 120 words: communication style, interests, routines, goals (known facts only)\",\"detail\":50,\"play\":40,\"topics\":[\"up to 3 topics to learn next\"],\"upgrades\":[\"up to 3 features that would help this user\"],\"summary\":\"one sentence\"}}. Merge only true duplicates. Never invent facts.", True))
    if not o: raise RuntimeError("Could not read my own reflection")
    settings.put("prev", {"mem": mems, "profile": settings.get("profile", ""), "style": settings.get("style", {"detail": 50, "play": 40})})
    byid = {m["id"]: m for m in mems}; merged = 0
    for g in o.get("merges") or []:
        ids = [i for i in (g.get("ids") or []) if i in byid]
        if len(ids) > 1 and g.get("text"):
            for i in ids: memory.delete(i)
            memory.add("long_term", str(g["text"]), "merged"); merged += 1
    if o.get("profile"): settings.put("profile", str(o["profile"])[:800])
    st = settings.get("style", {"detail": 50, "play": 40})
    for k in ("detail", "play"):
        if isinstance(o.get(k), (int, float)): st[k] = max(0, min(100, round(st[k] * .5 + o[k] * .5)))
    settings.put("style", st); settings.put("sugg", [str(t) for t in (o.get("topics") or [])[:3]]); settings.put("upg", [str(t) for t in (o.get("upgrades") or [])[:3]])
    settings.put("refl", settings.get("refl", 0) + 1); log("Reflected: " + str(o.get("summary") or "refined my understanding of you") + (f" (merged {merged})" if merged else ""))
    return o
def undo():
    p = settings.get("prev")
    if not p: return False
    db.q("DELETE FROM memories")
    for m in p["mem"]: db.q("INSERT INTO memories(id,level,content,tags,created,updated) VALUES(?,?,?,?,?,?)", (m["id"], m["level"], m["content"], m["tags"], m["created"], m["updated"]))
    settings.put("profile", p["profile"]); settings.put("style", p["style"]); settings.put("prev", None); log("Undid the last reflection"); return True
def state(): return {k: settings.get(k, d) for k, d in (("auto", None), ("profile", ""), ("style", {"detail": 50, "play": 40}), ("sugg", []), ("upg", []), ("log", []), ("turns", 0), ("refl", 0))} | {"can_undo": bool(settings.get("prev"))}
