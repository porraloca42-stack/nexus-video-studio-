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
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    # edge-tts changed SubMaker's public API: current releases
                    # accept the complete event via feed(); older releases used
                    # create_sub((offset, duration), text).
                    feed = getattr(maker, "feed", None)
                    if callable(feed):
                        feed(chunk)
                    else:
                        create_sub = getattr(maker, "create_sub", None)
                        if not callable(create_sub):
                            raise RuntimeError(
                                "A versão instalada do edge-tts não oferece "
                                "feed() nem create_sub() para gerar legendas."
                            )
                        create_sub(
                            (chunk["offset"], chunk["duration"]),
                            chunk["text"],
                        )

        # Current edge-tts exposes get_srt(); older releases exposed
        # generate_subs(). Keep both paths for environments with pinned caches.
        get_srt = getattr(maker, "get_srt", None)
        if callable(get_srt):
            subtitle_text = get_srt()
        else:
            generate_subs = getattr(maker, "generate_subs", None)
            if callable(generate_subs):
                subtitle_text = generate_subs()
            else:
                raise RuntimeError(
                    "A versão instalada do edge-tts não oferece get_srt() "
                    "nem generate_subs() para finalizar as legendas."
                )
        subtitles.write_text(subtitle_text, encoding="utf-8")
    asyncio.run(generate())
    return output, subtitles
