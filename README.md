# showhn-github-viewer

A command-line tool for browsing **Show HN** posts that feature GitHub
repositories.  
Results are fetched from the [HN Algolia API](https://hn.algolia.com/api) and
displayed in an interactive TUI.

---

## Features

- **GitHub Focused**: Automatically filters Show HN posts to show only those with GitHub repository links.
- **Interactive TUI**: Browse posts with a clean terminal interface.
- **README Preview**: Press `Enter` to open a vertical split-pane showing the repository's `README.md` directly in your terminal.
- **Relative Time**: Displays how long ago projects were posted.

---

## Usage

```bash
# Run directly using uvx (recommended)
uvx --from . showhn-github-viewer
```

Or run the script directly:

```bash
uv run showhn [OPTIONS]
```

### Options

```
Options:
  -p, --page INTEGER   Initial page number (0-indexed, default: 0)
  --help               Show this message and exit
```

### Examples

```bash
# View the latest 20 Show HN GitHub posts
showhn

# Jump straight to page 3
showhn --page 2
```

### Controls

#### Navigation
- `↑` / `k`: Move selection up (or scroll README up if open)
- `↓` / `j`: Move selection down (or scroll README down if open)
- `n` / `→`: Next page
- `p` / `←`: Previous page
- `q`: Quit

#### README Pane
- `Enter`: Toggle README preview pane for the selected project
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
