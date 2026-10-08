# VoiceBox (local) text-to-speech helper. Uses the "Teacher" profile (Kokoro preset voice af_heart).
import json, os, subprocess, time, urllib.request as u
BASE = "http://127.0.0.1:17493"; HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"C:\Program Files\Voicebox\voicebox-server.exe"; DATA = os.path.join(HERE, "voicebox-data")

def _req(path, body=None, method=None, timeout=300, raw=False):
    r = u.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json"}, method=method)
    with u.urlopen(r, timeout=timeout) as resp: data = resp.read(); return data if raw else json.loads(data)

def ensure_server():
    try: _req("/health", timeout=3); return
    except Exception: pass
    os.makedirs(DATA, exist_ok=True)
    subprocess.Popen([EXE, "--host", "127.0.0.1", "--port", "17493", "--data-dir", DATA], stdout=open(os.path.join(DATA, "server.log"), "a"), stderr=subprocess.STDOUT, creationflags=0x08000000)
    for _ in range(120):
        try: _req("/health", timeout=3); return
        except Exception: time.sleep(3)
    raise RuntimeError("VoiceBox server did not start")

def profile_id():
    for p in _req("/profiles"):
        if p["name"] == "Teacher": return p["id"]
    return _req("/profiles", {"name": "Teacher", "description": "Warm, clear teacher voice for OpenPrep", "language": "en", "voice_type": "preset", "preset_engine": "kokoro", "preset_voice_id": "af_heart", "default_engine": "kokoro"})["id"]

def ensure_model():
    st = {m["model_name"]: m for m in _req("/models/status").get("models", [])}
    if not st.get("kokoro", {}).get("downloaded"):
        _req("/models/download", {"model_name": "kokoro"})
        for _ in range(600):
            time.sleep(3)
            st = {m["model_name"]: m for m in _req("/models/status").get("models", [])}
            if st.get("kokoro", {}).get("downloaded"): break

def speak(text, out_path):
    """Generate speech for `text` and save a WAV at out_path."""
    ensure_server(); ensure_model()
    g = _req("/generate", {"profile_id": profile_id(), "text": text, "language": "en", "engine": "kokoro", "normalize": True})
    gid = g["id"]
    for _ in range(1800):
        h = _req(f"/history/{gid}", timeout=60)
        if h.get("status") == "completed": break
        if h.get("status") == "failed": raise RuntimeError(str(h.get("error"))[:300])
        time.sleep(1)
    else: raise RuntimeError("generation timed out")
    open(out_path, "wb").write(_req(f"/audio/{gid}", raw=True)); return out_path

if __name__ == "__main__":
    import sys; print(speak(sys.argv[1], sys.argv[2]))
