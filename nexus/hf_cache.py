"""Hugging Face cache-aware download helper with explicit timing metrics."""
from __future__ import annotations

import time
from typing import Any, Callable, Type


def download_with_cache_metrics(
    download_fn: Callable[..., Any],
    cache_miss_exception: Type[BaseException],
    **download_kwargs: Any,
) -> dict:
    """Prefer a local Hugging Face cache hit; download only on a true cache miss.

    The caller supplies LocalEntryNotFoundError from huggingface_hub.errors.
    Other failures (network/auth/repository/file errors) intentionally bubble up.
    """
    lookup_started = time.monotonic()
    try:
        path = download_fn(**download_kwargs, local_files_only=True)
        return {
            "path": path,
            "cache_hit": True,
            "cache_lookup_seconds": round(time.monotonic() - lookup_started, 3),
            "download_seconds": 0.0,
        }
    except cache_miss_exception:
        lookup_seconds = round(time.monotonic() - lookup_started, 3)
        download_started = time.monotonic()
        path = download_fn(**download_kwargs)
        return {
            "path": path,
            "cache_hit": False,
            "cache_lookup_seconds": lookup_seconds,
            "download_seconds": round(time.monotonic() - download_started, 3),
        }
