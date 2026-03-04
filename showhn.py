#!/usr/bin/env python3
"""Show HN GitHub Viewer - Browse Show HN posts featuring GitHub repos."""

import sys
import time

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

    Results are fetched from hn.algolia.com and displayed in a pager.
    Use --page / -p to jump to a specific page.
    """
    current_page = page

    while True:
        click.echo(f"Fetching page {current_page + 1}…", err=True)
        try:
            data = fetch_stories(page=current_page)
        except requests.RequestException as exc:
            click.echo(f"Error fetching data: {exc}", err=True)
            sys.exit(1)

        hits = data.get("hits", [])
        num_pages = data.get("nbPages", 1)

        if not hits:
            click.echo("No results found.", err=True)
            break

        content = build_page_content(hits, current_page, num_pages)
        click.echo_via_pager(content)

        break


if __name__ == "__main__":
    main()
