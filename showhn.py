#!/usr/bin/env python3
"""Show HN GitHub Viewer - Browse Show HN posts featuring GitHub repos."""

import curses
import sys
import time
from typing import Optional

import click
import requests

API_URL = "https://hn.algolia.com/api/v1/search_by_date"
HITS_PER_PAGE = 20


def fetch_stories(page: int = 0) -> dict:
    """Fetch Show HN stories from HN Algolia API."""
    params = {
        "query": "show hn github",
        "tags": "story",
        "hitsPerPage": HITS_PER_PAGE,
        "page": page,
    }
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


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


def _safe_addnstr(stdscr, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
    """Add text safely in curses windows without crashing on size limits."""
    if width <= 0:
        return
    try:
        stdscr.addnstr(y, x, text, width, attr)
    except curses.error:
        pass


def draw_tui(stdscr, hits: list, selected_idx: int, page: int, num_pages: int) -> None:
    """Draw the TUI list view."""
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    header = (
        f"Show HN GitHub Viewer [Page {page + 1}/{num_pages}] "
        "↑/k ↓/j: move  n/p: page  q: quit"
    )
    _safe_addnstr(stdscr, 0, 0, header, width - 1)

    list_height = max(1, height - 3)
    start_idx = 0
    if selected_idx >= list_height:
        start_idx = selected_idx - list_height + 1

    end_idx = min(len(hits), start_idx + list_height)
    for row, i in enumerate(range(start_idx, end_idx), start=1):
        story = hits[i]
        line = format_story_line(page * HITS_PER_PAGE + i + 1, story)
        attr = curses.A_REVERSE if i == selected_idx else curses.A_NORMAL
        _safe_addnstr(stdscr, row, 0, line, width - 1, attr)

    selected_story = hits[selected_idx]
    selected_url = selected_story.get("url") or "(no URL)"
    _safe_addnstr(stdscr, height - 1, 0, f"URL: {selected_url}", width - 1)

    stdscr.refresh()


def run_tui(initial_page: int = 0, initial_data: Optional[dict] = None) -> None:
    """Run interactive TUI for browsing Show HN results."""

    def _parse(data: dict) -> tuple[list, int]:
        hits = data.get("hits", [])
        num_pages = data.get("nbPages", 1) or 1
        return hits, max(1, int(num_pages))

    def _app(stdscr) -> None:
        current_page = initial_page
        selected_idx = 0
        data = initial_data if initial_data is not None else fetch_stories(page=current_page)
        hits, num_pages = _parse(data)

        stdscr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass

        while True:
            draw_tui(stdscr, hits, selected_idx, current_page, num_pages)
            key = stdscr.getch()

            if key in (ord("q"),):
                return
            if key in (curses.KEY_UP, ord("k")) and selected_idx > 0:
                selected_idx -= 1
                continue
            if key in (curses.KEY_DOWN, ord("j")) and selected_idx < len(hits) - 1:
                selected_idx += 1
                continue
            if key in (ord("n"), curses.KEY_RIGHT) and current_page + 1 < num_pages:
                current_page += 1
                data = fetch_stories(page=current_page)
                hits, num_pages = _parse(data)
                selected_idx = 0
                continue
            if key in (ord("p"), curses.KEY_LEFT) and current_page > 0:
                current_page -= 1
                data = fetch_stories(page=current_page)
                hits, num_pages = _parse(data)
                selected_idx = 0

    curses.wrapper(_app)


@click.command()
@click.option(
    "--page",
    "-p",
    default=0,
    show_default=True,
    help="Page number (0-indexed).",
)
def main(page: int) -> None:
    """Browse Show HN posts that feature GitHub repositories.

    Results are fetched from hn.algolia.com and displayed in a TUI.
    Use --page / -p to choose the initial page.
    """
    try:
        data = fetch_stories(page=page)
    except requests.RequestException as exc:
        click.echo(f"Error fetching data: {exc}", err=True)
        sys.exit(1)

    hits = data.get("hits", [])
    if not hits:
        click.echo("No results found.", err=True)
        return

    try:
        run_tui(initial_page=page, initial_data=data)
    except requests.RequestException as exc:
        click.echo(f"Error fetching data: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
