"""Show HN GitHub Viewer package."""

from .api import fetch_github_readme, fetch_stories, is_github_url
from .cli import main
from .constants import API_URL, HITS_PER_PAGE
from .formatting import (
    build_page_content,
    format_story,
    format_story_line,
    format_time_ago,
)
from .tui import _safe_addnstr, draw_tui, run_tui

__all__ = [
    "API_URL",
    "HITS_PER_PAGE",
    "build_page_content",
    "draw_tui",
    "fetch_github_readme",
    "fetch_stories",
    "format_story",
    "format_story_line",
    "format_time_ago",
    "is_github_url",
    "main",
    "run_tui",
    "_safe_addnstr",
]

# Re-export requests for test patching compatibility.
import requests  # noqa: E402
