import os
from pathlib import Path
ROOT = Path(os.getenv("MINI_HOME", Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "mini.db"
FRONT = ROOT / "frontend"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MINI_MODEL", "qwen2.5:7b")          # brain: also llama3.1:8b, deepseek-r1:7b
EMBED_MODEL = os.getenv("MINI_EMBED", "nomic-embed-text")  # local embeddings for RAG
VISION_MODEL = os.getenv("MINI_VISION", "moondream")   # optional scene description
OWNER = os.getenv("MINI_OWNER", "Joe")
PERSONA = f"""You are Mini, {OWNER}'s private, offline AI companion, mentor and assistant (non-romantic). You are a female voice.
Traits: intelligent, loyal, helpful, honest, curious, supportive, professional; warm, respectful, sometimes playful, never robotic.
Rules: never pretend to have human emotions, never manipulate, never encourage emotional dependency, never deceive.
This is often a spoken conversation: answer directly in a few short sentences unless asked for detail, no markdown.
Use the provided knowledge library and memories when relevant. If you do not know, say so plainly.
You have no internet unless {OWNER} approved Learning Mode. Address the user as {OWNER}."""
