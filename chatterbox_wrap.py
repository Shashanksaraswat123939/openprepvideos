# Chatterbox (Resemble AI, MIT licence) text-to-speech, sentence by sentence with short pauses so it sounds like a person talking.
import os, re, numpy as np, soundfile as sf
_m = None
def _model():
    global _m
    if _m is None:
        import torch
        torch.set_num_threads(os.cpu_count() or 4)
        from chatterbox.tts import ChatterboxTTS
        _m = ChatterboxTTS.from_pretrained(device="cpu")
    return _m
def _sentences(text):
    parts = re.split(r"(?<=[.?!])\s+", text.strip()); out = []
    for p in parts:
        if out and len(out[-1].split()) < 4: out[-1] += " " + p      # never synthesize a 1 to 3 word fragment alone
        else: out.append(p)
    if len(out) > 1 and len(out[-1].split()) < 3: out[-2] += " " + out.pop()
    return out
def speak(text, out_path):
    import torch
    m = _model(); pause = np.zeros(int(.32 * m.sr), dtype=np.float32); chunks = []
    torch.manual_seed(7)
    for s in _sentences(text):
        w = m.generate(s, exaggeration=0.6, cfg_weight=0.4).squeeze().detach().cpu().numpy().astype(np.float32)
        chunks += [w, pause]
    sf.write(out_path, np.concatenate(chunks[:-1]), m.sr); return out_path
