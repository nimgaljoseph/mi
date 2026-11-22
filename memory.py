from .db import q
LEVELS = ["short_term", "long_term", "knowledge", "episodic"]
def add(level, content, tags=""):
    assert level in LEVELS; return q("INSERT INTO memories(level,content,tags) VALUES(?,?,?)", (level, content, tags))
def search(text="", level=None, limit=50):
    sql, a = "SELECT * FROM memories WHERE content LIKE ?", [f"%{text}%"]
    if level: sql += " AND level=?"; a.append(level)
    return q(sql + " ORDER BY updated DESC LIMIT ?", (*a, limit))
def relevant(message, k=6):
    words = [w for w in message.lower().split() if len(w) > 3][:8]
    seen, out = set(), []
    for w in words:
        for m in search(w, limit=k):
            if m["id"] not in seen: seen.add(m["id"]); out.append(m)
    return out[:k]
def edit(i, content): q("UPDATE memories SET content=?, updated=CURRENT_TIMESTAMP WHERE id=?", (content, i))
def delete(i): q("DELETE FROM memories WHERE id=?", (i,))
def merge(ids, content):
    new = add("long_term", content, "merged")
    for i in ids: delete(i)
    return new
def stats(): return q("SELECT level, COUNT(*) n FROM memories GROUP BY level")
def export(): return q("SELECT * FROM memories ORDER BY id")
