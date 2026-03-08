"""Formatting helpers for Show HN GitHub Viewer."""

import time

from .constants import HITS_PER_PAGE


def format_time_ago(created_at_i: int) -> str:
    """Format Unix timestamp as human-readable relative time.

    Uses approximate durations (30-day month, 365-day year) which is
    acceptable for a display-only "time ago" label.
    """
    diff = int(time.time()) - created_at_i

    if diff < 60:
        return f"{diff} second{'s' if diff != 1 else ''} ago"
    elif diff < 3600:
        minutes = diff // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = diff // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < 86400 * 30:
        days = diff // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < 86400 * 365:
        months = diff // (86400 * 30)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff // (86400 * 365)
        return f"{years} year{'s' if years != 1 else ''} ago"


def format_story(index: int, story: dict) -> str:
    """Format a single story for display."""
    title = story.get("title") or "No title"
    url = story.get("url") or "(no URL)"
    points = story.get("points") or 0
    created_at_i = story.get("created_at_i") or 0
    time_ago = format_time_ago(created_at_i)

    return (
        f"{index:>3}. {title}\n"
        f"     URL:    {url}\n"
        f"     Points: {points} | {time_ago}\n"
    )


def format_story_line(index: int, story: dict) -> str:
    """Format a single story as one line for TUI list view."""
    title = story.get("title") or "No title"
    points = story.get("points") or 0
    created_at_i = story.get("created_at_i") or 0
    time_ago = format_time_ago(created_at_i)
    return f"{index:>3}. {title} ({points} pts, {time_ago})"


def build_page_content(hits: list, page: int, num_pages: int) -> str:
    """Build the full text content for one page of results."""
    lines = [
        f"=== Show HN GitHub Viewer  [Page {page + 1} / {num_pages}] ===\n",
    ]
    for i, story in enumerate(hits, start=page * HITS_PER_PAGE + 1):
        lines.append(format_story(i, story))

    footer = f"--- End of page {page + 1} ---"
    if page + 1 < num_pages:
        footer += "  (run with --page to navigate)"
    lines.append(footer)
    return "\n".join(lines)
