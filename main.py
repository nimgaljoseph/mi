import asyncio, base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import db, memory, permissions, llm, learning, rag, vision, brain, evolve, settings
from .config import OWNER, FRONT, MODEL
db.init()
app = FastAPI(title="Mini")
class Chat(BaseModel): message: str; seen: list[str] = []
class Mem(BaseModel): level: str = "long_term"; content: str; tags: str = ""
class Merge(BaseModel): ids: list[int]; content: str
class Decision(BaseModel): decision: str; detail: str = ""
class Topic(BaseModel): topic: str
class Task(BaseModel): title: str; kind: str = "task"; due: str | None = None
class Text(BaseModel): name: str; text: str
class Enroll(BaseModel): name: str; kind: str = "person"; image: str
class Frame(BaseModel): image: str
class Flag(BaseModel): value: bool
def jpeg(s): return base64.b64decode(s.split(",")[-1])
def fail(e, code=400): raise HTTPException(code, str(e))

@app.get("/api/status")
async def status():
    return {"owner": OWNER, "llm": await llm.status(), "permissions": permissions.all_states(), "memory": memory.stats(), "vision_ready": vision.ready(), "docs": len(rag.docs())}
@app.post("/api/chat")
async def chat(b: Chat):
    hist = [{"role": r["role"], "content": r["content"]} for r in db.q("SELECT role,content FROM conversations ORDER BY id DESC LIMIT 12")][::-1]
    try: reply, sources = await brain.think(hist, b.message, b.seen)
    except Exception as e: fail(f"My local brain isn't responding ({type(e).__name__}). Is Ollama running and is the model '{MODEL}' pulled?", 503)
    db.q("INSERT INTO conversations(role,content) VALUES('user',?)", (b.message,)); db.q("INSERT INTO conversations(role,content) VALUES('assistant',?)", (reply,))
    n = settings.get("turns", 0) + 1; settings.put("turns", n)
    if settings.get("auto"):
        if n % 3 == 0: asyncio.create_task(_safe(evolve.autolearn(OWNER)))
        if n % 12 == 0: asyncio.create_task(_safe(evolve.reflect(OWNER)))
    return {"reply": reply, "sources": sources}
async def _safe(c):
    try: await c
    except Exception: pass
@app.get("/api/conversations")
def convs(): return db.q("SELECT * FROM conversations ORDER BY id DESC LIMIT 50")
@app.get("/api/permissions")
def perms(): return {"states": permissions.all_states(), "audit": db.q("SELECT * FROM audit ORDER BY id DESC LIMIT 30")}
@app.post("/api/permissions/{name}")
def perm(name: str, d: Decision):
    if name not in permissions.PERMS or d.decision not in ("allow_once", "always_allow", "deny"): fail("bad request")
    permissions.decide(name, d.decision, d.detail); return permissions.all_states()
@app.delete("/api/permissions/{name}")
def revoke(name: str): permissions.set_mode(name, "ask", "reset/ended"); return permissions.all_states()
@app.get("/api/memory")
def mem_search(q: str = "", level: str | None = None): return memory.search(q, level)
@app.post("/api/memory")
def mem_add(m: Mem): return {"id": memory.add(m.level, m.content, m.tags)}
@app.put("/api/memory/{i}")
def mem_edit(i: int, m: Mem): memory.edit(i, m.content); return {"ok": True}
@app.delete("/api/memory/{i}")
def mem_del(i: int): memory.delete(i); return {"ok": True}
@app.post("/api/memory/merge")
def mem_merge(m: Merge): return {"id": memory.merge(m.ids, m.content)}
@app.get("/api/memory-export")
def mem_export(): return memory.export()
# knowledge library (RAG)
@app.post("/api/knowledge/upload")
async def upload(files: list[UploadFile] = File(...)):
    out = []
    for f in files:
        try: out.append(await rag.add_text(f.filename, rag.extract(f.filename, await f.read()), "upload"))
        except Exception as e: out.append({"name": f.filename, "error": str(e)})
    return out
@app.post("/api/knowledge/text")
async def kt(t: Text):
    try: return await rag.add_text(t.name, t.text, "note")
    except Exception as e: fail(e)
@app.get("/api/knowledge")
def kl(): return rag.docs()
@app.get("/api/knowledge/search")
async def ks(q: str): return await rag.search(q, 6)
@app.delete("/api/knowledge/{i}")
def kd(i: int): rag.delete(i); return {"ok": True}
@app.post("/api/learn")
async def learn(b: Topic):
    try: return await learning.learn(b.topic)
    except HTTPException as e:
        if isinstance(e.detail, dict): return {"needs_permission": "internet", "prompt": f"I need internet access to learn about {b.topic}. Allow?"}
        raise
    except Exception as e: fail(f"Learning failed: {e}", 502)
# vision (offline)
@app.post("/api/vision/enroll")
def enroll(b: Enroll):
    permissions.active("camera")
    try: return {"samples": vision.enroll(b.name.strip(), "person" if b.kind == "person" else "pet", jpeg(b.image))}
    except RuntimeError as e: fail(e, 503)
    except Exception as e: fail(e)
@app.post("/api/vision/recognize")
def recognize(b: Frame):
    permissions.active("camera")
    try: return vision.recognize(jpeg(b.image))
    except RuntimeError as e: fail(e, 503)
    except Exception as e: fail(e)
@app.post("/api/vision/describe")
async def describe(b: Frame):
    permissions.active("camera")
    try: return {"text": await llm.describe(b.image.split(",")[-1])}
    except Exception as e: fail(f"Scene description needs a local vision model: run 'ollama pull moondream' ({e})", 503)
@app.get("/api/vision/known")
def known(): return vision.known()
@app.delete("/api/vision/known/{name}")
def forget(name: str): vision.forget(name); return {"ok": True}
# voice in (offline Whisper)
@app.post("/api/stt")
async def stt(audio: UploadFile = File(...)):
    permissions.active("microphone")
    try:
        from . import stt as S
        return {"text": await asyncio.to_thread(S.transcribe, await audio.read())}
    except ImportError: fail("Offline speech needs: pip install -r backend/requirements-voice.txt", 501)
    except Exception as e: fail(e, 500)
# evolution
@app.get("/api/evolve")
def ev(): return evolve.state()
@app.post("/api/evolve/auto")
def ev_auto(f: Flag): settings.put("auto", f.value); return evolve.state()
@app.post("/api/evolve/reflect")
async def ev_reflect():
    try: await evolve.reflect(OWNER)
    except Exception as e: fail(e, 503)
    return evolve.state()
@app.post("/api/evolve/undo")
def ev_undo(): evolve.undo(); return evolve.state()
@app.get("/api/tasks")
def tasks(): return db.q("SELECT * FROM tasks ORDER BY done, id DESC")
@app.post("/api/tasks")
def task_add(t: Task): return {"id": db.q("INSERT INTO tasks(title,kind,due) VALUES(?,?,?)", (t.title, t.kind, t.due))}
@app.post("/api/tasks/{i}/toggle")
def task_toggle(i: int): db.q("UPDATE tasks SET done=1-done WHERE id=?", (i,)); return {"ok": True}
@app.delete("/api/tasks/{i}")
def task_del(i: int): db.q("DELETE FROM tasks WHERE id=?", (i,)); return {"ok": True}
@app.get("/")
def index(): return FileResponse(FRONT / "index.html")
app.mount("/static", StaticFiles(directory=FRONT), name="static")
