import asyncio, edge_tts
TEXT = ("Step one. Read the question first, so you know what it is asking. Then look for the turn word, such as however or but. "
        "That word usually points to the real idea, and it is where most students lose the point. Let's try it together.")
VOICES = {"A_ava": "en-US-AvaMultilingualNeural", "B_andrew": "en-US-AndrewMultilingualNeural", "C_emma": "en-US-EmmaMultilingualNeural",
          "D_brian": "en-US-BrianMultilingualNeural", "E_aria": "en-US-AriaNeural", "F_sonia_uk": "en-GB-SoniaNeural"}
async def main():
    for k, v in VOICES.items():
        await edge_tts.Communicate(TEXT, v, rate="-4%").save(f"voice_samples/{k}.mp3"); print("ok", k)
asyncio.run(main())
