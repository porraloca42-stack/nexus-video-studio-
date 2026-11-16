import subprocess
import tempfile
from pathlib import Path

WIDTH, HEIGHT, FPS = 720, 1280, 30

def run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result

def normalize_clip(source, destination, duration, motion="push_in"):
    frames = max(1, int(float(duration) * FPS))
    if motion == "pan_left":
        zoom = "1.06"
        x = f"iw/2-(iw/zoom/2)+(iw/zoom/2)*on/{frames}"
    elif motion == "pan_right":
        zoom = "1.06"
        x = f"iw/2-(iw/zoom/2)-(iw/zoom/2)*on/{frames}"
    elif motion == "pull_out":
        zoom = "max(1.0,1.08-on*0.0008)"
        x = "iw/2-(iw/zoom/2)"
    else:
        zoom = "min(zoom+0.0008,1.08)"
        x = "iw/2-(iw/zoom/2)"
    filter_graph = (
        f"scale=900:1600:force_original_aspect_ratio=increase,crop=900:1600,"
        f"zoompan=z='{zoom}':x='{x}':y='ih/2-(ih/zoom/2)':d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "eq=contrast=1.04:saturation=1.04:brightness=0.005,setsar=1,format=yuv420p"
    )
    run(["ffmpeg", "-y", "-i", str(source), "-t", str(duration), "-vf", filter_graph, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", str(destination)])

def render_video(media, audio_path, output, subtitles_path=None):
    if not media:
        raise ValueError("Nenhuma cena foi aprovada.")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nexus_render_") as temp_dir:
        temp_dir = Path(temp_dir)
        clips = []
        for index, item in enumerate(media):
            clip = temp_dir / f"scene_{index:02d}.mp4"
            normalize_clip(item["path"], clip, item["duration"], item.get("camera_motion", "push_in"))
            clips.append(clip)
        concat = temp_dir / "concat.txt"
        concat.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in clips), encoding="utf-8")
        silent = temp_dir / "joined.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(silent)])
        command = ["ffmpeg", "-y", "-i", str(silent), "-i", str(audio_path)]
        if subtitles_path and Path(subtitles_path).exists():
            subtitle_file = str(Path(subtitles_path).resolve()).replace("\\", "/").replace(":", "\\:")
            subtitle_filter = f"subtitles='{subtitle_file}':force_style='FontName=Arial,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=105,Bold=1'"
            command += ["-vf", subtitle_filter]
        command += ["-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(output)]
        run(command)
    return output
