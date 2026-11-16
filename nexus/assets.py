import requests
from pathlib import Path

def search_pexels_videos(query, api_key, per_page=15):
    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": per_page, "orientation": "portrait"},
        timeout=45,
    )
    response.raise_for_status()
    results = []
    for item in response.json().get("videos", []):
        files = item.get("video_files", [])
        usable = [f for f in files if f.get("link") and f.get("width", 0) >= 480 and f.get("height", 0) >= 700]
        if not usable:
            continue
        usable.sort(key=lambda f: (f.get("width", 0) >= 720, f.get("width", 0) * f.get("height", 0)), reverse=True)
        results.append({"url": usable[0]["link"], "width": usable[0].get("width"), "height": usable[0].get("height")})
    return results

def download_file(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    output.write(chunk)
    return destination
