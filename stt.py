import os, tempfile
_m = None
def transcribe(data):
    global _m
    from faster_whisper import WhisperModel      # pip install -r requirements-voice.txt
    if _m is None: _m = WhisperModel(os.getenv("MINI_STT", "base.en"), device="cpu", compute_type="int8")
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f: f.write(data); p = f.name
    try:
        segs, _ = _m.transcribe(p, language="en", vad_filter=True)
        return " ".join(s.text.strip() for s in segs).strip()
    finally: os.unlink(p)
