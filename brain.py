from . import memory, rag, llm, settings
async def think(history, message, seen=()):
    parts = []
    prof = settings.get("profile", "")
    if prof: parts.append("What you have learned about the user's style, interests and goals:\n" + prof)
    st = settings.get("style", {"detail": 50, "play": 40})
    parts.append(f"Preferred answer detail {st['detail']}/100 (low means very brief), playfulness {st['play']}/100.")
    mems = memory.relevant(message)
    if mems: parts.append("Things you remember:\n" + "\n".join(f"- {m['content'][:400]}" for m in mems))
    docs = await rag.search(message)
    if docs: parts.append("Relevant material from the user's own knowledge library (prefer it, mention the source name):\n" + "\n".join(f"[{d['doc']}] {d['text']}" for d in docs))
    if seen: parts.append("Through the camera you can currently see: " + ", ".join(seen) + ".")
    return await llm.chat(history, message, "\n\n" + "\n\n".join(parts)), [d["doc"] for d in docs]
