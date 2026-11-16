import re
import requests
from pathlib import Path

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "by",
    "with", "from", "for", "over", "under", "into", "through", "during",
    "person", "people", "man", "woman", "someone", "cinematic", "wide",
    "shot", "footage", "video", "realistic", "beautiful", "professional",
    "showing", "shows", "scene", "close", "up", "dark", "room", "macro",
    "heavy", "fast", "early", "turning", "off", "looking", "out", "high",
    "apartment", "cozy", "light", "sweat"
}

# Stock libraries index simple subjects and actions more reliably than full cinematic prompts.
def build_query_variants(query, max_variants=6):
    original = re.sub(r"\s+", " ", str(query or "")).strip()
    if not original:
        return []
    variants = []
    seen = set()

    def add(value):
        value = re.sub(r"\s+", " ", str(value or "")).strip()
        key = value.casefold()
        if value and key not in seen and len(variants) < max_variants:
            seen.add(key)
            variants.append(value)

    add(original)
    words = re.findall(r"[a-zA-Z0-9]+", original.lower())
    keywords = [word for word in words if word not in _STOPWORDS and len(word) > 2]
    # Search variants come only from the director's scene-specific query.
    # No fixed topic dictionary or hardcoded visual themes.
    add(" ".join(keywords[:4]))
    for word in keywords:
        add(word)
        if len(variants) >= max_variants:
            break
    return variants

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

def _query_tokens(value):
    words = re.findall(r"[a-zA-Z0-9]+", str(value or "").lower())
    return [word for word in words if word not in _STOPWORDS and len(word) > 2]


def rank_video_candidates(candidates, query):
    """Rank stock results by scene-query relevance before technical quality."""
    query_terms = list(dict.fromkeys(_query_tokens(query)))
    if not query_terms:
        query_terms = []
    for item in candidates:
        title_terms = set(_query_tokens(item.get("title", "")))
        description_terms = set(_query_tokens(item.get("description", "")))
        matched_title = len(set(query_terms) & title_terms)
        matched_description = len(set(query_terms) & description_terms)
        matched_terms = len(set(query_terms) & (title_terms | description_terms))
        coverage = (matched_title + matched_description) / max(1, len(query_terms))
        # Semantic text relevance outranks orientation/resolution; technical
        # quality is only a tie-breaker and must not promote unrelated stock.
        item["_nexus_match_count"] = matched_terms
        item["_nexus_relevance"] = (
            matched_title * 4.0
            + matched_description * 1.5
            + coverage * 3.0
        )
        item["_nexus_quality"] = (
            1 if item.get("vertical") else 0,
            min(int(item.get("height") or 0), 2160),
            min(int(item.get("width") or 0), 2160),
        )
    return sorted(
        candidates,
        key=lambda item: (item["_nexus_relevance"], *item["_nexus_quality"]),
        reverse=True,
    )


def search_video_sources(
    query,
    coverr_key='',
    pixabay_key='',
    per_page=20,
    exclude_urls=None,
    relevance_query=None,
    min_relevance=1.5,
):
    """Search stock libraries, rejecting results with no scene-level text match."""
    errors = []
    excluded = set(exclude_urls or [])
    variants = build_query_variants(query, max_variants=4)
    semantic_query = relevance_query if relevance_query is not None else query

    def usable(results, source, search_query):
        unique = []
        seen = set(excluded)
        for item in results:
            url = item.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            item["matched_query"] = search_query
            item["source"] = item.get("source") or source
            unique.append(item)
        ranked = rank_video_candidates(unique, semantic_query)
        # Require at least two distinct scene terms when the query has two or
        # more meaningful terms. A one-term query still needs that one match.
        required_matches = min(2, len(_query_tokens(semantic_query)))
        # Do not silently accept unrelated stock merely because the API
        # returned something. Continue with shorter search variants instead.
        return [
            item for item in ranked
            if item.get("_nexus_relevance", 0.0) >= float(min_relevance)
            and item.get("_nexus_match_count", 0) >= required_matches
        ]

    if coverr_key:
        for search_query in variants:
            try:
                results = search_coverr_videos(search_query, coverr_key, per_page)
                ranked = usable(results, "Coverr", search_query)
                if ranked:
                    return ranked, errors
            except requests.RequestException as exc:
                errors.append(f'Coverr ({search_query}): {exc}')
    if pixabay_key:
        for search_query in variants:
            try:
                results = search_pixabay_videos(search_query, pixabay_key, per_page)
                ranked = usable(results, "Pixabay", search_query)
                if ranked:
                    return ranked, errors
            except requests.RequestException as exc:
                errors.append(f'Pixabay ({search_query}): {exc}')
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
