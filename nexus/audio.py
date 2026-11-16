import asyncio
from pathlib import Path
import edge_tts

def make_voice(text, voice, output):
    output = Path(output)
    subtitles = output.with_suffix(".srt")
    async def generate():
        communicate = edge_tts.Communicate(text, voice)
        maker = edge_tts.SubMaker()
        with output.open("wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    maker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
        subtitles.write_text(maker.generate_subs(), encoding="utf-8")
    asyncio.run(generate())
    return output, subtitles
