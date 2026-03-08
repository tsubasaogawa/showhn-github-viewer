"""CLI entrypoint for Show HN GitHub Viewer."""

import sys

import click
import requests

from .api import fetch_stories, is_github_url
from .tui import run_tui


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
    # Filter only GitHub URLs
    hits = [h for h in hits if is_github_url(h.get("url"))]
    data["hits"] = hits

    if not hits:
        click.echo("No results found.", err=True)
        return

    try:
        run_tui(initial_page=page, initial_data=data)
    except requests.RequestException as exc:
        click.echo(f"Error fetching data: {exc}", err=True)
        sys.exit(1)
