import httpx
from .config import OLLAMA_URL, MODEL, PERSONA, VISION_MODEL, EMBED_MODEL
async def _post(path, body, t=300):
    async with httpx.AsyncClient(timeout=t) as c:
        r = await c.post(f"{OLLAMA_URL}{path}", json=body); r.raise_for_status(); return r.json()
async def chat(history, message, extra=""):
    msgs = [{"role": "system", "content": PERSONA + extra}, *history[-12:], {"role": "user", "content": message}]
    return (await _post("/api/chat", {"model": MODEL, "messages": msgs, "stream": False}))["message"]["content"]
async def generate(prompt, json_mode=False):
    body = {"model": MODEL, "prompt": prompt, "stream": False}
    if json_mode: body["format"] = "json"
    return (await _post("/api/generate", body))["response"]
async def embed(texts): return (await _post("/api/embed", {"model": EMBED_MODEL, "input": texts}))["embeddings"]
async def describe(b64, prompt="Describe what you see briefly."):
    r = await _post("/api/chat", {"model": VISION_MODEL, "stream": False, "messages": [{"role": "user", "content": prompt, "images": [b64]}]})
    return r["message"]["content"]
async def status():
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            names = [m["name"] for m in (await c.get(f"{OLLAMA_URL}/api/tags")).json()["models"]]
        return {"ollama": True, "models": names, "brain": MODEL, "embed_ready": any(EMBED_MODEL in n for n in names), "brain_ready": any(MODEL.split(":")[0] in n for n in names)}
    except Exception: return {"ollama": False, "models": [], "brain": MODEL, "embed_ready": False, "brain_ready": False}
