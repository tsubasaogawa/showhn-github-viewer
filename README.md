# showhn-github-viewer

A command-line tool for browsing **Show HN** posts that feature GitHub
repositories.  
Results are fetched from the [HN Algolia API](https://hn.algolia.com/api) and
displayed in an interactive TUI.

---

## Features

- GitHub Focused: Automatically filters Show HN posts to show only those with GitHub repository links.
- Interactive TUI: Browse posts with a clean terminal interface.
- README Preview: Press `Enter` to open a vertical split-pane showing the repository's `README.md` directly in your terminal.
- Open in Browser: Press `o` to open the selected project's URL in your default browser.
- Filtering: Press `f` to filter results by a minimum number of points.
- Relative Time: Displays how long ago projects were posted.

---

## Usage

```bash
# Run directly using uvx (recommended)
uvx --from git+https://github.com/tsubasaogawa/showhn-github-viewer main
```

Or run the script directly:

```bash
# Clone this repo and run the following:
uv run main [OPTIONS]
```

### Controls

#### Navigation
- `↑` / `k`: Move selection up (or scroll README up if open)
- `↓` / `j`: Move selection down (or scroll README down if open)
- `n` / `→`: Next page
- `p` / `←`: Previous page
- `q`: Quit

#### Actions
- `Enter`: Toggle README preview pane for the selected project
- `o`: Open the selected project's URL in your default browser
- `f`: Set a minimum point threshold for filtering results

#### README Pane
- `u` / `d`: Scroll README up/down by half a page
- `PgUp` / `PgDn`: Scroll README up/down by a full page

---

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for information on setting up the development environment, running tests, and project structure.

## Background

Hacker News' *Show HN* section features many open-source GitHub projects.
The standard search at
[hn.algolia.com](https://hn.algolia.com/?dateRange=all&page=0&prefix=true&query=show%20hn%20github&sort=byDate&type=story)
works but is inconvenient to browse.  
This tool focuses solely on GitHub Show HN posts and provides a clean,
paginated terminal interface with instant project previews.
