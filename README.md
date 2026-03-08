# showhn-github-viewer

A command-line tool for browsing **Show HN** posts that feature GitHub
repositories.  
Results are fetched from the [HN Algolia API](https://hn.algolia.com/api) and
displayed in an interactive TUI.

---

## Usage

```bash
# Run directly using uvx (recommended)
uvx --from . showhn-github-viewer
```

Or run the script directly:

```bash
uv run showhn.py [OPTIONS]
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

### Display

Each result shows:

```
  1. Show HN: My Awesome Project
     URL:    https://github.com/user/my-awesome-project
     Points: 312 | 3 hours ago
```

Results are displayed in an interactive terminal UI.

- `↑` / `k`: move selection up
- `↓` / `j`: move selection down
- `n` / `→`: next page
- `p` / `←`: previous page
- `q`: quit

---

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for information on setting up the development environment, running tests, and project structure.

## Background

Hacker News' *Show HN* section features many open-source GitHub projects.
The standard search at
[hn.algolia.com](https://hn.algolia.com/?dateRange=all&page=0&prefix=true&query=show%20hn%20github&sort=byDate&type=story)
works but is inconvenient to browse.  
This tool focuses solely on GitHub Show HN posts and provides a clean,
paginated terminal interface.
