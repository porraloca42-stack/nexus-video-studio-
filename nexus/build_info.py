"""Runtime build identity without contacting external services."""
import os
import re
import subprocess
from pathlib import Path
from typing import Mapping, Optional, Tuple

_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_ENV_SHA_NAMES = (
    "STREAMLIT_GIT_SHA",
    "GIT_COMMIT_SHA",
    "COMMIT_SHA",
    "GITHUB_SHA",
    "SOURCE_VERSION",
)


def _valid_sha(value: object) -> Optional[str]:
    candidate = str(value or "").strip()
    if _SHA_RE.fullmatch(candidate):
        return candidate.lower()
    return None


def get_runtime_build_info(
    repository_root: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Return (commit_sha, source); never substitute the remote branch HEAD.

    The checked-out Git worktree is authoritative. Known CI/deployment SHA
    variables are a fallback for platforms that omit the .git directory.
    """
    root = Path(repository_root or Path(__file__).resolve().parents[1])
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        sha = _valid_sha(result.stdout) if result.returncode == 0 else None
        if sha:
            return sha, "git"
    except (OSError, subprocess.SubprocessError):
        pass

    env = environ if environ is not None else os.environ
    for name in _ENV_SHA_NAMES:
        sha = _valid_sha(env.get(name))
        if sha:
            return sha, name
    return None, None
