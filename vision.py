"""Offline recognition. People: YuNet detector + SFace embeddings. Pets/objects: MobileNetV2 embeddings (approximate)."""
import cv2, numpy as np
from .config import ROOT
from .db import q
M = ROOT / "models"
FILES = ("face_detection_yunet_2023mar.onnx", "face_recognition_sface_2021dec.onnx", "mobilenetv2-12.onnx")
PERSON_T, PET_T = 0.363, 0.80
_det = _rec = _net = None
def ready(): return all((M / f).exists() for f in FILES)
def _load():
    global _det, _rec, _net
    if _det is None:
        miss = [f for f in FILES if not (M / f).exists()]
        if miss: raise RuntimeError("Missing vision models: " + ", ".join(miss) + ". Run scripts\\download_models.bat")
        _det = cv2.FaceDetectorYN.create(str(M / FILES[0]), "", (320, 320), 0.8)
        _rec = cv2.FaceRecognizerSF.create(str(M / FILES[1]), "")
        _net = cv2.dnn.readNetFromONNX(str(M / FILES[2]))
def _img(b):
    im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
    if im is None: raise ValueError("Could not read that image")
    return im
def _faces(im):
    h, w = im.shape[:2]; _det.setInputSize((w, h)); _, f = _det.detect(im)
    return [] if f is None else list(f)
def _fvec(im, f): return _rec.feature(_rec.alignCrop(im, f)).flatten().astype(np.float32)
def _pvec(im):
    blob = cv2.dnn.blobFromImage(cv2.resize(im, (224, 224)), 1 / 58.0, (224, 224), (123.675, 116.28, 103.53), swapRB=True)
    _net.setInput(blob); v = _net.forward().flatten().astype(np.float32); return v - v.mean()
def _cos(a, b): return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
def enroll(name, kind, data):
    _load(); im = _img(data)
    if kind == "person":
        fs = _faces(im)
        if not fs: raise ValueError("I can't see a face in that frame. Face the camera in good light.")
        v = _fvec(im, max(fs, key=lambda f: f[2] * f[3]))
    else: v = _pvec(im)
    q("INSERT INTO faces(name,kind,vec) VALUES(?,?,?)", (name, kind, v.tobytes()))
    return q("SELECT COUNT(*) n FROM faces WHERE name=?", (name,))[0]["n"]
def recognize(data):
    _load(); im = _img(data); rows = q("SELECT name,kind,vec FROM faces")
    people = [(r["name"], np.frombuffer(r["vec"], np.float32)) for r in rows if r["kind"] == "person"]
    pets = [(r["name"], r["kind"], np.frombuffer(r["vec"], np.float32)) for r in rows if r["kind"] != "person"]
    out = {"faces": [], "pets": []}
    for f in _faces(im):
        v, best, name = _fvec(im, f), 0.0, "unknown"
        for n, pv in people:
            s = _cos(v, pv)
            if s > best: best, name = s, n
        out["faces"].append({"name": name if best >= PERSON_T else "unknown", "score": round(best, 3), "box": [int(x) for x in f[:4]]})
    if pets and not out["faces"]:
        v, best, name = _pvec(im), -1.0, None
        for n, k, pv in pets:
            s = _cos(v, pv)
            if s > best: best, name = s, n
        if best >= PET_T: out["pets"].append({"name": name, "score": round(best, 3)})
    return out
def known(): return q("SELECT name,kind,COUNT(*) samples FROM faces GROUP BY name,kind ORDER BY name")
def forget(name): q("DELETE FROM faces WHERE name=?", (name,))
