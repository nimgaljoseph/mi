"""Learning Mode: internet is used ONLY here, after permission; the grant is then consumed, and the result is stored locally for offline use."""
import httpx
from . import permissions, rag, llm
async def learn(topic):
    permissions.require("internet", f"learn: {topic}")
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": "MiniCompanion/1.0"}) as c:
        s = await c.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "list": "search", "srsearch": topic, "format": "json", "srlimit": 3})
        titles = [h["title"] for h in s.json()["query"]["search"]]; texts = []
        for t in titles:
            e = await c.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "prop": "extracts", "explaintext": 1, "exlimit": 1, "titles": t, "format": "json"})
            texts += [p.get("extract", "")[:8000] for p in e.json()["query"]["pages"].values()]
    permissions.set_mode("internet", "ask", "learning finished, internet closed")
    summary = await llm.generate(f"Write a structured study summary of '{topic}' from these sources:\n\n" + "\n\n".join(texts))
    doc = await rag.add_text(f"Learned: {topic}", summary + "\n\nSources: " + ", ".join(titles), "learned")
    return {"topic": topic, "sources": titles, "summary": summary, "doc": doc}
