# Kokoro text-to-speech used on Linux / Codespaces (same voice as the VoiceBox "Teacher" profile: af_heart).
import numpy as np, soundfile as sf
_pipe = None
def speak(text, out_path):
    global _pipe
    if _pipe is None:
        from kokoro import KPipeline
        _pipe = KPipeline(lang_code="a")
    parts = []
    for _, _, audio in _pipe(text, voice="af_heart", speed=1.0):
        parts.append(audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio))
    sf.write(out_path, np.concatenate(parts), 24000)
    return out_path
