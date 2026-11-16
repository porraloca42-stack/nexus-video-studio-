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

def _commons_metadata_value(metadata, key):
    value = (metadata.get(key) or {}).get("value", "")
    return re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", str(value))).strip()


def search_wikimedia_videos(query, per_page=20):
    """Search Commons video files and keep only clearly commercial-use licenses.

    To avoid ambiguous reuse conditions in commercial creator workflows, this
    adapter accepts CC0, public-domain and CC BY (not BY-SA, NC or ND) files.
    """
    response = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:video {query}",
            "gsrnamespace": 6,
            "gsrlimit": min(max(int(per_page), 1), 20),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "format": "json",
            "formatversion": 2,
        },
        headers={"User-Agent": "NEXUSVideoStudio/1.0 (https://github.com/porraloca42-stack/nexus-video-studio-)"},
        timeout=45,
    )
    response.raise_for_status()
    pages = (response.json().get("query") or {}).get("pages") or []
    if isinstance(pages, dict):
        pages = list(pages.values())

    results = []
    allowed_extensions = (".webm", ".ogv", ".mpg", ".mpeg")
    for page in pages:
        info_list = page.get("imageinfo") or []
        if not info_list:
            continue
        info = info_list[0]
        url = info.get("url", "")
        mime = str(info.get("mime") or "").lower()
        if not url or not url.lower().split("?", 1)[0].endswith(allowed_extensions):
            continue
        if mime and not mime.startswith("video/"):
            continue

        metadata = info.get("extmetadata") or {}
        license_name = _commons_metadata_value(metadata, "LicenseShortName")
        license_url = _commons_metadata_value(metadata, "LicenseUrl")
        normalized_license = license_name.casefold().replace("-", " ").strip()
        is_cc0 = "cc0" in normalized_license or "cc zero" in normalized_license
        is_public_domain = "public domain" in normalized_license
        is_cc_by = (
            "cc by" in normalized_license
            and "sa" not in normalized_license
            and "nc" not in normalized_license
            and "nd" not in normalized_license
        )
        if not (is_cc0 or is_public_domain or is_cc_by):
            continue

        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        if width < 320 or height < 240:
            continue
        title = str(page.get("title") or "").removeprefix("File:")
        author = _commons_metadata_value(metadata, "Artist")
        credit = _commons_metadata_value(metadata, "Credit")
        description_url = info.get("descriptionurl") or (
            "https://commons.wikimedia.org/wiki/" + str(page.get("title", "")).replace(" ", "_")
        )
        results.append({
            "url": url,
            "width": width,
            "height": height,
            "vertical": height > width,
            "title": title,
            "description": _commons_metadata_value(metadata, "ImageDescription"),
            "source": "Wikimedia Commons",
            "source_url": description_url,
            "author": author,
            "author_url": "",
            "license": license_name,
            "license_url": license_url,
            "credit": credit or author,
            "attribution_required": bool(is_cc_by),
        })
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


def search_pexels_videos(query, api_key, per_page=20):
    """Search Pexels video library and normalize results to the NEXUS asset schema."""
    response = requests.get(
        "https://api.pexels.com/v1/videos/search",
        headers={"Authorization": api_key},
        params={
            "query": query,
            "orientation": "portrait",
            "locale": "pt-BR",
            "per_page": min(int(per_page), 80),
        },
        timeout=45,
    )
    response.raise_for_status()
    results = []
    for item in response.json().get("videos", []):
        files = [
            video_file for video_file in item.get("video_files", [])
            if video_file.get("link")
            and video_file.get("file_type") == "video/mp4"
            and int(video_file.get("width") or 0) >= 480
            and int(video_file.get("height") or 0) >= 700
        ]
        if not files:
            continue
        files.sort(
            key=lambda video_file: (
                1 if str(video_file.get("quality", "")).lower() in {"hd", "uhd"} else 0,
                int(video_file.get("width") or 0) * int(video_file.get("height") or 0),
            ),
            reverse=True,
        )
        chosen = files[0]
        user = item.get("user") or {}
        results.append({
            "url": chosen["link"],
            "width": int(chosen.get("width") or 0),
            "height": int(chosen.get("height") or 0),
            "vertical": int(chosen.get("height") or 0) > int(chosen.get("width") or 0),
            "title": item.get("alt") or "",
            "description": item.get("alt") or "",
            "source": "Pexels",
            "source_url": item.get("url") or "https://www.pexels.com/videos/",
            "author": user.get("name") or "",
            "author_url": user.get("url") or "",
        })
    return results

def _query_tokens(value):
    words = re.findall(r"[a-zA-Z0-9]+", str(value or "").lower())
    return [word for word in words if word not in _STOPWORDS and len(word) > 2]


def rank_video_candidates(candidates, query, style_query=""):
    """Rank narration/scene relevance first; visual style is only a secondary signal."""
    query_terms = list(dict.fromkeys(_query_tokens(query)))
    style_terms = list(dict.fromkeys(_query_tokens(style_query)))
    for item in candidates:
        title_terms = set(_query_tokens(item.get("title", "")))
        description_terms = set(_query_tokens(item.get("description", "")))
        metadata_terms = title_terms | description_terms
        matched_title = len(set(query_terms) & title_terms)
        matched_description = len(set(query_terms) & description_terms)
        matched_terms = len(set(query_terms) & metadata_terms)
        coverage = (matched_title + matched_description) / max(1, len(query_terms))
        style_matches = len(set(style_terms) & metadata_terms)
        style_coverage = style_matches / max(1, len(style_terms))
        # Narration/scene relevance is the primary sort key. Style can only
        # break ties; resolution and orientation come after both.
        item["_nexus_match_count"] = matched_terms
        item["_nexus_relevance"] = (
            matched_title * 4.0
            + matched_description * 1.5
            + coverage * 3.0
        )
        item["_nexus_style_relevance"] = style_matches * 2.0 + style_coverage
        width = max(0, int(item.get("width") or 0))
        height = max(0, int(item.get("height") or 0))
        ratio = (width / height) if width and height else 0.0
        target_ratio = 9 / 16
        # Prefer true portrait footage and, within that group, frames closest
        # to the 9:16 delivery canvas. Semantic relevance remains the primary key.
        aspect_fit = max(0.0, 1.0 - abs(ratio - target_ratio) / target_ratio) if ratio else 0.0
        item["_nexus_aspect_ratio"] = round(ratio, 4) if ratio else None
        item["_nexus_aspect_fit"] = round(aspect_fit, 4)
        item["_nexus_quality"] = (
            1 if height > width else 0,
            aspect_fit,
            min(height, 2160),
            min(width, 2160),
        )
    return sorted(
        candidates,
        key=lambda item: (
            item["_nexus_relevance"],
            item["_nexus_style_relevance"],
            *item["_nexus_quality"],
        ),
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
    pexels_key='',
    style_query='',
    wikimedia_enabled=False,
):
    """Search every enabled library for scene content and style, then rank together."""
    errors = []
    excluded = set(exclude_urls or [])
    semantic_query = relevance_query if relevance_query is not None else query
    variants = build_query_variants(query, max_variants=5)
    # Search the requested style independently so it cannot dilute the
    # narration query. The style query never qualifies an unrelated clip alone.
    style_variants = build_query_variants(style_query, max_variants=1)
    search_variants = [(value, True) for value in variants] + [
        (value, False) for value in style_variants if value.casefold() not in {v.casefold() for v in variants}
    ]
    query_terms = list(dict.fromkeys(_query_tokens(semantic_query)))
    all_candidates = []

    sources = []
    if wikimedia_enabled:
        sources.append(("Wikimedia Commons", search_wikimedia_videos, ""))
    if coverr_key:
        sources.append(("Coverr", search_coverr_videos, coverr_key))
    if pixabay_key:
        sources.append(("Pixabay", search_pixabay_videos, pixabay_key))
    if pexels_key:
        sources.append(("Pexels", search_pexels_videos, pexels_key))

    # Query every enabled provider. Do not return early when the first
    # provider finds a match: the final choice must compare the whole pool.
    for source_name, search_fn, api_key in sources:
        for search_query, is_scene_query in search_variants:
            try:
                results = search_fn(search_query, api_key, per_page)
                for item in results:
                    url = item.get("url")
                    if not url or url in excluded:
                        continue
                    item["matched_query"] = search_query
                    item["matched_scene_query"] = bool(is_scene_query)
                    item["source"] = item.get("source") or source_name
                    all_candidates.append(item)
            except requests.RequestException as exc:
                response = getattr(exc, "response", None)
                status_code = getattr(response, "status_code", None)
                errors.append(f"{source_name} ({search_query}): {exc}")
                # Authentication/permission failures will not be fixed by trying
                # more query variants with the same credential.
                if status_code in (401, 403):
                    errors.append(
                        f"{source_name}: HTTP {status_code}; interrompi novas consultas "
                        "nesta biblioteca. Verifique a chave e as permissões da API."
                    )
                    break

    # Deduplicate identical downloads while preserving provider provenance
    # and whether the asset came from a scene query or a style-only query.
    deduplicated = {}
    for item in all_candidates:
        url = item["url"]
        existing = deduplicated.get(url)
        if existing is None:
            deduplicated[url] = item
        else:
            providers = set(existing.get("also_found_by", []))
            providers.add(item.get("source", ""))
            existing["also_found_by"] = sorted(name for name in providers if name)
            existing["matched_scene_query"] = (
                existing.get("matched_scene_query", False)
                or item.get("matched_scene_query", False)
            )

    # A result returned by a scene-specific query is a retrieval candidate,
    # even when its stock-library title/tags use different wording or language.
    # The visual reviewer inspects actual frames and rejects unrelated clips.
    # Style-only search results are admitted only if their metadata also has
    # a meaningful overlap with the scene brief.
    ranked_all = rank_video_candidates(
        list(deduplicated.values()), semantic_query, style_query=style_query
    )
    scene_candidates = [
        item for item in ranked_all
        if item.get("matched_scene_query")
        or (
            len(query_terms) >= 2
            and item.get("_nexus_match_count", 0) >= 1
        )
    ]
    return scene_candidates, errors

def download_file(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(
        url,
        stream=True,
        timeout=120,
        headers={"User-Agent": "NEXUSVideoStudio/1.0 (https://github.com/porraloca42-stack/nexus-video-studio-)"},
    ) as response:
        response.raise_for_status()
        with destination.open('wb') as output:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    output.write(chunk)
    return destination


def diverse_candidate_shortlist(candidates, limit=6):
    """Compare the strongest result from each configured library before repeats."""
    ranked = sorted(
        candidates or [],
        key=lambda item: (
            float(item.get("_nexus_relevance", 0.0)),
            float(item.get("_nexus_style_relevance", 0.0)),
            1 if item.get("vertical") else 0,
            int(item.get("height") or 0),
        ),
        reverse=True,
    )
    selected, seen_sources, seen_urls = [], set(), set()
    for item in ranked:
        source = str(item.get("source") or "Unknown")
        if source not in seen_sources and item.get("url") not in seen_urls:
            selected.append(item)
            seen_sources.add(source)
            seen_urls.add(item.get("url"))
            if len(selected) >= max(1, int(limit)):
                return selected
    for item in ranked:
        if item.get("url") in seen_urls:
            continue
        selected.append(item)
        seen_urls.add(item.get("url"))
        if len(selected) >= max(1, int(limit)):
            break
    return selected
