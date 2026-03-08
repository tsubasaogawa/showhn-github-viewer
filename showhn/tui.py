"""Curses-based TUI for browsing Show HN results."""

import curses
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
) -> None:
    """Draw the TUI list view."""
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    if height < 3 or width < 10:
        return

    header = (
        "Show HN GitHub Viewer [P{}/{}] "
        "↑↓/kj: move/scroll  Enter: toggle  u/d/PgUp/PgDn: scroll  n/p: page  q: quit"
    ).format(page + 1, num_pages)
    # Pad header to full width with reverse attribute
    header_padded = header.ljust(width - 1)[: width - 1]
    _safe_addnstr(stdscr, 0, 0, header_padded, width - 1, curses.A_REVERSE)

    list_width = width // 2 if readme_lines is not None else width

    # Use all available middle space for the list
    list_height = height - 2
    start_idx = 0
    if selected_idx >= list_height:
        start_idx = selected_idx - list_height + 1

    end_idx = min(len(hits), start_idx + list_height)
    for row_offset, i in enumerate(range(start_idx, end_idx)):
        story = hits[i]
        line = format_story_line(page * HITS_PER_PAGE + i + 1, story)
        attr = curses.A_REVERSE if i == selected_idx else curses.A_NORMAL

        # Pad selected line to full width
        if i == selected_idx:
            line_to_draw = line.ljust(list_width - 1)[: list_width - 1]
        else:
            line_to_draw = line[: list_width - 1]

        _safe_addnstr(stdscr, row_offset + 1, 0, line_to_draw, list_width - 1, attr)

        if readme_lines is not None:
            # Draw a vertical separator
            _safe_addnstr(stdscr, row_offset + 1, list_width - 1, "|", 1, curses.A_DIM)

    # Draw README pane if open
    if readme_lines is not None:
        readme_width = width - list_width
        for row_offset in range(list_height):
            line_idx = readme_scroll + row_offset
            if line_idx < len(readme_lines):
                line_to_draw = readme_lines[line_idx].replace("\t", "    ")[: readme_width - 1]
                _safe_addnstr(
                    stdscr, row_offset + 1, list_width, line_to_draw, readme_width - 1
                )

    # Footer at the very bottom
    selected_story = hits[selected_idx]
    selected_url = selected_story.get("url") or "(no URL)"
    footer = f"URL: {selected_url}"
    footer_padded = footer.ljust(width - 1)[: width - 1]
    _safe_addnstr(stdscr, height - 1, 0, footer_padded, width - 1, curses.A_REVERSE)

    stdscr.refresh()


def run_tui(initial_page: int = 0, initial_data: Optional[dict] = None) -> None:
    """Run interactive TUI for browsing Show HN results."""

    def _parse(data: dict) -> tuple[list, int]:
        hits = data.get("hits", [])
        # Filter only GitHub URLs
        hits = [h for h in hits if is_github_url(h.get("url"))]
        num_pages = data.get("nbPages", 1) or 1
        return hits, max(1, int(num_pages))

    def _app(stdscr) -> None:
        current_page = initial_page
        selected_idx = 0
        data = initial_data if initial_data is not None else fetch_stories(page=current_page)
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
                data = fetch_stories(page=current_page)
                hits, num_pages = _parse(data)
                selected_idx = 0
                readme_lines = None
                continue
            if key in (ord("p"), curses.KEY_LEFT) and current_page > 0:
                current_page -= 1
                data = fetch_stories(page=current_page)
                hits, num_pages = _parse(data)
                selected_idx = 0
                readme_lines = None

    curses.wrapper(_app)
