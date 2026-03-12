"""API helpers for fetching Show HN data and GitHub README."""

from typing import Optional
from urllib.parse import urlparse

import requests

from .constants import API_URL, HITS_PER_PAGE


def is_github_url(url: Optional[str]) -> bool:
    """Check if the URL belongs to github.com."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.netloc == "github.com"
    except Exception:
        return False


def fetch_github_readme(url: str) -> Optional[str]:
    """Fetch README.md from a GitHub repository."""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            response = requests.get(
                api_url,
                headers={"Accept": "application/vnd.github.v3.raw"},
                timeout=5,
            )
            if response.status_code == 200:
                return response.text
    except Exception:
        pass
    return None


def fetch_stories(page: int = 0, min_points: Optional[int] = None) -> dict:
    """Fetch Show HN stories from HN Algolia API."""
    params = {
        "query": "show hn github",
        "tags": "story",
        "hitsPerPage": HITS_PER_PAGE,
        "page": page,
    }
    if min_points is not None:
        params["numericFilters"] = f"points>={min_points}"
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
