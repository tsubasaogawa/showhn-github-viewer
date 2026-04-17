"""CLI entrypoint for Show HN GitHub Viewer."""

import sys
from typing import Optional

import click
import requests


@click.command()
@click.option(
    "--page",
    "-p",
    default=0,
    show_default=True,
    help="Page number (0-indexed).",
)
@click.option(
    "--filter",
    "min_points",
    type=click.IntRange(min=0),
    default=None,
    help="Minimum points filter.",
)
@click.option(
    "--num",
    "hits_per_page",
    type=click.IntRange(min=1),
    default=20,
    show_default=True,
    help="Number of stories to display per page.",
)
def main(page: int, min_points: Optional[int], hits_per_page: int) -> None:
    """Browse Show HN posts that feature GitHub repositories.

    Results are fetched from hn.algolia.com and displayed in a TUI.
    Use --page / -p to choose the initial page.
    """
    import src as package

    try:
        data = package.fetch_stories(
            page=page,
            min_points=min_points,
            hits_per_page=hits_per_page,
        )
    except requests.RequestException as exc:
        click.echo(f"Error fetching data: {exc}", err=True)
        sys.exit(1)

    hits = data.get("hits", [])
    # Filter only GitHub URLs
    hits = [h for h in hits if package.is_github_url(h.get("url"))]
    data["hits"] = hits

    if not hits:
        click.echo("No results found.", err=True)
        return

    try:
        package.run_tui(
            initial_page=page,
            initial_data=data,
            initial_min_points=min_points,
            hits_per_page=hits_per_page,
        )
    except requests.RequestException as exc:
        click.echo(f"Error fetching data: {exc}", err=True)
        sys.exit(1)
