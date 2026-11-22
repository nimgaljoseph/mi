import io, re, zipfile
import numpy as np
from xml.etree import ElementTree as ET
from .db import q
from . import llm
def chunk(text, size=900, overlap=150):
    text = re.sub(r"[ \t]+", " ", text).strip(); out, i = [], 0
    while i < len(text): out.append(text[i:i + size]); i += size - overlap
    return out
def extract(filename, data):
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    if ext == "docx":
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        x = ET.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"))
        return "\n".join("".join(t.text or "" for t in p.iter(ns + "t")) for p in x.iter(ns + "p"))
    return data.decode("utf-8", "ignore")
async def add_text(name, text, kind="note"):
    ch = chunk(text)
    if not ch: raise ValueError("No readable text found in that file")
    doc = q("INSERT INTO docs(name,kind) VALUES(?,?)", (name, kind))
    try: embs = await llm.embed(ch)
    except Exception: embs = [None] * len(ch)     # keyword search still works without the embedding model
    for t, e in zip(ch, embs):
        q("INSERT INTO chunks(doc_id,text,emb) VALUES(?,?,?)", (doc, t, np.asarray(e, dtype=np.float32).tobytes() if e else None))
    return {"id": doc, "name": name, "chunks": len(ch), "semantic": embs[0] is not None}
async def search(query, k=4):
    rows = q("SELECT c.text,c.emb,d.name FROM chunks c JOIN docs d ON d.id=c.doc_id")
    if not rows: return []
    try:
        qe = np.asarray((await llm.embed([query]))[0], dtype=np.float32); qe /= np.linalg.norm(qe) + 1e-9
        sc = [float(np.frombuffer(r["emb"], dtype=np.float32) @ qe / (np.linalg.norm(np.frombuffer(r["emb"], dtype=np.float32)) + 1e-9)) if r["emb"] else -1 for r in rows]
        floor = 0.40
    except Exception:
        w = re.findall(r"\w{4,}", query.lower()); sc = [sum(x in r["text"].lower() for x in w) / (len(w) or 1) for r in rows]; floor = 0.3
    top = sorted(zip(sc, rows), key=lambda x: -x[0])[:k]
    return [{"doc": r["name"], "text": r["text"], "score": round(s, 3)} for s, r in top if s >= floor]
def docs(): return q("SELECT d.id,d.name,d.kind,d.created,(SELECT COUNT(*) FROM chunks WHERE doc_id=d.id) chunks FROM docs d ORDER BY d.id DESC")
def delete(i): q("DELETE FROM chunks WHERE doc_id=?", (i,)); q("DELETE FROM docs WHERE id=?", (i,))
