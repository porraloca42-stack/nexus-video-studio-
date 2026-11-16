import requests
from pathlib import Path

def search_coverr_videos(query, api_key, per_page=20):
    response = requests.get('https://api.coverr.co/videos', headers={'x-api-key': api_key}, params={'query': query, 'page': 0, 'page_size': per_page, 'urls': 'true'}, timeout=45)
    response.raise_for_status()
    results = []
    for item in response.json().get('hits', []):
        urls = item.get('urls') or {}
        url = urls.get('mp4_download') or urls.get('mp4')
        if not url:
            continue
        width, height = int(item.get('max_width') or 0), int(item.get('max_height') or 0)
        results.append({'url': url, 'width': width, 'height': height, 'vertical': bool(item.get('is_vertical')), 'title': item.get('title', ''), 'description': item.get('description', ''), 'source': 'Coverr', 'source_url': 'https://coverr.co/videos/' + item.get('id', '')})
    results.sort(key=lambda x: (x['vertical'], x['height'] >= 720, x['width'] * x['height']), reverse=True)
    return results

def search_pixabay_videos(query, api_key, per_page=20):
    response = requests.get('https://pixabay.com/api/videos/', params={'key': api_key, 'q': query, 'per_page': per_page, 'safesearch': 'true'}, timeout=45)
    response.raise_for_status()
    results = []
    for item in response.json().get('hits', []):
        usable = []
        for variant in (item.get('videos') or {}).values():
            url, width, height = variant.get('url'), int(variant.get('width') or 0), int(variant.get('height') or 0)
            if url and width >= 480 and height >= 700:
                usable.append({'url': url, 'width': width, 'height': height})
        if usable:
            usable.sort(key=lambda x: (x['width'] >= 720, x['width'] * x['height']), reverse=True)
            chosen = usable[0]
            results.append({**chosen, 'vertical': chosen['height'] > chosen['width'], 'title': item.get('tags', ''), 'description': item.get('tags', ''), 'source': 'Pixabay', 'source_url': item.get('pageURL', 'https://pixabay.com/videos/')})
    results.sort(key=lambda x: (x['vertical'], x['width'] * x['height']), reverse=True)
    return results

def search_video_sources(query, coverr_key='', pixabay_key='', per_page=20):
    errors = []
    if coverr_key:
        try:
            results = search_coverr_videos(query, coverr_key, per_page)
            if results:
                return results, errors
        except requests.RequestException as exc:
            errors.append('Coverr: ' + str(exc))
    if pixabay_key:
        try:
            results = search_pixabay_videos(query, pixabay_key, per_page)
            if results:
                return results, errors
        except requests.RequestException as exc:
            errors.append('Pixabay: ' + str(exc))
    return [], errors

def download_file(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open('wb') as output:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    output.write(chunk)
    return destination
