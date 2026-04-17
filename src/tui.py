"""Curses-based TUI for browsing Show HN results."""

import curses
import webbrowser
from typing import Optional

from .api import fetch_github_readme, fetch_stories, is_github_url
from .constants import HITS_PER_PAGE
from .formatting import format_story_line


def _safe_addnstr(stdscr, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
    """Add text safely in curses windows without crashing on size limits."""
    if width <= 0:
        return
    try:
        stdscr.addnstr(y, x, text, width, attr)
    except curses.error:
        pass


def draw_tui(
    stdscr,
    hits: list,
    selected_idx: int,
    page: int,
    num_pages: int,
    readme_lines: Optional[list[str]] = None,
    readme_scroll: int = 0,
    min_points: Optional[int] = None,
    hits_per_page: int = HITS_PER_PAGE,
) -> None:
    """Draw the TUI list view."""
    import src as package

    def fill_row(y: int, x: int, segment_width: int, text: str = "", attr: int = 0) -> None:
        """Fill a row segment so panes visually occupy the available space."""
        if segment_width <= 0:
            return
        package._safe_addnstr(
            stdscr,
            y,
            x,
            text.ljust(segment_width)[:segment_width],
            segment_width,
            attr,
        )

    stdscr.erase()
    height, width = stdscr.getmaxyx()

    if height < 3 or width < 10:
        return

    filter_text = f" [Pts>={min_points}]" if min_points is not None else ""
    header = (
        f"Show HN GitHub Viewer{filter_text} [P{page + 1}/{num_pages}] "
        "↑↓/kj: move/scroll  Enter: toggle  o: open  f: filter  u/d: scroll  n/p: page  q: quit"
    )
    fill_row(0, 0, width, header, curses.A_REVERSE)

    list_height = height - 2
    list_width = width
    divider_x = None
    readme_x = None
    readme_width = 0
    if readme_lines is not None:
        list_width = max(1, (width - 1) // 2)
        divider_x = list_width
        readme_x = divider_x + 1
        readme_width = max(0, width - readme_x)

    start_idx = 0
    if hits and selected_idx >= list_height:
        start_idx = selected_idx - list_height + 1

    end_idx = min(len(hits), start_idx + list_height)
    for row_offset in range(list_height):
        y = row_offset + 1
        hit_idx = start_idx + row_offset
        list_text = ""
        attr = curses.A_NORMAL

        if hit_idx < end_idx:
            story = hits[hit_idx]
            list_text = format_story_line(page * hits_per_page + hit_idx + 1, story)
            if hit_idx == selected_idx:
                attr = curses.A_REVERSE
        elif not hits and row_offset == list_height // 2:
            list_text = "No results found."

        fill_row(y, 0, list_width, list_text, attr)

        if readme_lines is not None and divider_x is not None and readme_x is not None:
            fill_row(y, divider_x, 1, "|", curses.A_DIM)
            readme_text = ""
            line_idx = readme_scroll + row_offset
            if line_idx < len(readme_lines):
                readme_text = readme_lines[line_idx].replace("\t", "    ")
            fill_row(y, readme_x, readme_width, readme_text)

    # Footer at the very bottom
    selected_story = hits[selected_idx] if hits else None
    selected_url = (
        (selected_story.get("url") or "(no URL)") if selected_story else "(no selection)"
    )
    footer = f"URL: {selected_url}"
    fill_row(height - 1, 0, width, footer, curses.A_REVERSE)

    stdscr.refresh()


def run_tui(
    initial_page: int = 0,
    initial_data: Optional[dict] = None,
    initial_min_points: Optional[int] = None,
    hits_per_page: int = HITS_PER_PAGE,
) -> None:
    """Run interactive TUI for browsing Show HN results."""

    def _parse(data: dict) -> tuple[list, int]:
        hits = data.get("hits", [])
        # Filter only GitHub URLs
        hits = [h for h in hits if is_github_url(h.get("url"))]
        num_pages = data.get("nbPages", 1) or 1
        return hits, max(1, int(num_pages))

    def _app(stdscr) -> None:
        current_page = initial_page
        min_points = initial_min_points
        selected_idx = 0
        data = (
            initial_data
            if initial_data is not None
            else fetch_stories(
                page=current_page,
                min_points=min_points,
                hits_per_page=hits_per_page,
            )
        )
        hits, num_pages = _parse(data)

        readme_lines = None
        readme_scroll = 0

        stdscr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass

        while True:
            draw_tui(
                stdscr,
                hits,
                selected_idx,
                current_page,
                num_pages,
                readme_lines,
                readme_scroll,
                min_points,
                hits_per_page,
            )
            key = stdscr.getch()

            if key in (ord("q"),):
                return
            if key == curses.KEY_RESIZE:
                continue
            if key in (curses.KEY_UP, ord("k")):
                if readme_lines is not None:
                    readme_scroll = max(0, readme_scroll - 1)
                elif selected_idx > 0:
                    selected_idx -= 1
                    readme_lines = None
                continue
            if key in (curses.KEY_DOWN, ord("j")):
                if readme_lines is not None:
                    readme_scroll = min(len(readme_lines) - 1, readme_scroll + 1)
                elif selected_idx < len(hits) - 1:
                    selected_idx += 1
                    readme_lines = None
                continue
            if key in (curses.KEY_ENTER, 10, 13):
                if not hits:
                    continue
                if readme_lines is None:
                    url = hits[selected_idx].get("url")
                    text = fetch_github_readme(url) if url else None
                    if text:
                        readme_lines = text.splitlines()
                    else:
                        readme_lines = ["(README not found or could not be fetched)"]
                    readme_scroll = 0
                else:
                    readme_lines = None
                continue
            if key == ord("o"):
                if not hits:
                    continue
                url = hits[selected_idx].get("url")
                if url:
                    webbrowser.open(url)
                continue
            if key == ord("f"):
                height, width = stdscr.getmaxyx()
                _safe_addnstr(stdscr, height - 1, 0, " " * (width - 1), width - 1, curses.A_NORMAL)
                _safe_addnstr(stdscr, height - 1, 0, "Min points: ", width - 1, curses.A_NORMAL)
                try:
                    curses.echo()
                    curses.curs_set(1)
                    s = stdscr.getstr(height - 1, 12, 10)
                    if s:
                        min_points = int(s.decode("utf-8").strip())
                    else:
                        min_points = None
                except (ValueError, curses.error):
                    min_points = None
                finally:
                    curses.noecho()
                    try:
                        curses.curs_set(0)
                    except curses.error:
                        pass
                
                current_page = 0
                data = fetch_stories(
                    page=current_page,
                    min_points=min_points,
                    hits_per_page=hits_per_page,
                )
                hits, num_pages = _parse(data)
                selected_idx = 0
                readme_lines = None
                readme_scroll = 0
                continue
            if key == ord("d") and readme_lines is not None:
                height, _ = stdscr.getmaxyx()
                readme_scroll = min(len(readme_lines) - 1, readme_scroll + (height - 2) // 2)
                continue
            if key == ord("u") and readme_lines is not None:
                height, _ = stdscr.getmaxyx()
                readme_scroll = max(0, readme_scroll - (height - 2) // 2)
                continue
            if key == curses.KEY_NPAGE and readme_lines is not None:
                height, _ = stdscr.getmaxyx()
                readme_scroll = min(len(readme_lines) - 1, readme_scroll + (height - 2))
                continue
            if key == curses.KEY_PPAGE and readme_lines is not None:
                height, _ = stdscr.getmaxyx()
                readme_scroll = max(0, readme_scroll - (height - 2))
                continue
            if key in (ord("n"), curses.KEY_RIGHT) and current_page + 1 < num_pages:
                current_page += 1
                data = fetch_stories(
                    page=current_page,
                    min_points=min_points,
                    hits_per_page=hits_per_page,
                )
                hits, num_pages = _parse(data)
                selected_idx = 0
                readme_lines = None
                readme_scroll = 0
                continue
            if key in (ord("p"), curses.KEY_LEFT) and current_page > 0:
                current_page -= 1
                data = fetch_stories(
                    page=current_page,
                    min_points=min_points,
                    hits_per_page=hits_per_page,
                )
                hits, num_pages = _parse(data)
                selected_idx = 0
                readme_lines = None
                readme_scroll = 0

    curses.wrapper(_app)
