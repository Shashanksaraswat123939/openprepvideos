"""Generate the same teaching lines with several free voice engines, so a human can pick the most natural one."""
import os, sys, time, json
OUT = "voice_lab_out"; os.makedirs(OUT, exist_ok=True)
STIFF = "Step one. Read the question first, so you know what it asks. Step two. Find the turn word, such as however or but."
SPOKEN = ("Okay, so here's the trick. Read the question first. Not the passage, the question. "
          "Because once you know what it's asking, the whole text suddenly makes sense. "
          "Then look for a turn word, like however, or but. That little word? It usually points right at the answer.")
log = {}
def timed(name, fn):
    t = time.time()
    try: fn(); log[name] = round(time.time() - t, 1); print("ok", name, log[name], flush=True)
    except Exception as e: log[name] = f"FAILED: {type(e).__name__}: {e}"[:300]; print("FAIL", name, e, flush=True)

# --- Chatterbox (Resemble AI, MIT licence, built in voice, no cloning of anyone)
def chatterbox():
    import torch, torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cpu")
    for tag, txt in (("stiff", STIFF), ("spoken", SPOKEN)):
        for ex, cfg in ((0.5, 0.5), (0.8, 0.3)):
            name = f"chatterbox_{tag}_ex{ex}_cfg{cfg}"
            t = time.time(); w = m.generate(txt, exaggeration=ex, cfg_weight=cfg); dt = time.time() - t
            ta.save(f"{OUT}/{name}.wav", w, m.sr); log[name + "_seconds_to_generate"] = round(dt, 1); log[name + "_audio_seconds"] = round(w.shape[-1] / m.sr, 1)
timed("chatterbox", chatterbox)

# --- Kokoro baseline and a blended, slower version
def kokoro():
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    p = KPipeline(lang_code="a")
    for tag, txt in (("stiff", STIFF), ("spoken", SPOKEN)):
        for vname, voice, sp in (("heart", "af_heart", 1.0), ("blend", "af_heart,af_bella", 0.93)):
            a = np.concatenate([x for _, _, x in p(txt, voice=voice, speed=sp)]); sf.write(f"{OUT}/kokoro_{tag}_{vname}.wav", a, 24000)
timed("kokoro", kokoro)

# --- Microsoft neural (for reference)
def edge():
    import asyncio, edge_tts
    async def go():
        for tag, txt in (("stiff", STIFF), ("spoken", SPOKEN)):
            await edge_tts.Communicate(txt, "en-US-AvaMultilingualNeural", rate="-4%").save(f"{OUT}/edge_ava_{tag}.mp3")
    asyncio.run(go())
timed("edge", edge)
json.dump(log, open(f"{OUT}/timings.json", "w"), indent=2); print(json.dumps(log, indent=2))
