"""Live smoke test for the public Wikimedia Commons video provider.

Calls the real Commons API, downloads one commercially reusable clip,
and verifies the media with FFprobe.
"""
import json
import subprocess
import tempfile
import sys
from pathlib import Path

# Running a file inside tests/ puts that directory first on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nexus.assets import download_file, search_wikimedia_videos


def main():
    candidates = search_wikimedia_videos("nature landscape", per_page=5)
    if not candidates:
        raise SystemExit("FAIL: Commons returned no video with an accepted license.")

    print(f"PASS: Commons search returned {len(candidates)} accepted video candidate(s).")
    for item in candidates[:5]:
        print(
            f"- {item.get('source')}: {item.get('title')} | "
            f"{item.get('width')}x{item.get('height')} | "
            f"{item.get('license')} | {item.get('source_url')}"
        )

    with tempfile.TemporaryDirectory(prefix="nexus_commons_smoke_") as temp:
        video_path = download_file(candidates[0]["url"], Path(temp) / "commons_smoke_video")
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height",
                "-of", "json", str(video_path),
            ],
            capture_output=True, text=True, timeout=90,
        )
        if probe.returncode != 0:
            raise SystemExit("FAIL: FFprobe could not read the downloaded Commons video: " + probe.stderr[-1000:])
        metadata = json.loads(probe.stdout)
        video = next((stream for stream in metadata.get("streams", []) if stream.get("codec_type") == "video"), None)
        duration = float(metadata.get("format", {}).get("duration") or 0)
        size = int(metadata.get("format", {}).get("size") or video_path.stat().st_size)
        if not video or duration <= 0 or size <= 0:
            raise SystemExit("FAIL: downloaded Commons asset has no valid video stream/duration/size.")
        print(
            f"PASS: downloaded and decoded video | {video.get('width')}x{video.get('height')} | "
            f"{duration:.2f}s | {size} bytes | {video.get('codec_name')}"
        )


if __name__ == "__main__":
    main()
