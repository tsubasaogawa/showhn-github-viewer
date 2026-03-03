# showhn-github-viewer

A command-line tool for browsing **Show HN** posts that feature GitHub
repositories.  
Results are fetched from the [HN Algolia API](https://hn.algolia.com/api) and
displayed in a pager (like `less`).

---

## Requirements

- Python 3.9+
- `pip`

## Installation

```bash
pip install -r requirements.txt
pip install -e .          # installs the `showhn` command
```

Or run directly without installing:

```bash
python showhn.py
```

## Usage

```
showhn [OPTIONS]

Options:
  -p, --page INTEGER   Page number to display (0-indexed, default: 0)
  -a, --all-pages      Interactively browse through all pages one by one
  --help               Show this message and exit
```

### Examples

```bash
# View the latest 20 Show HN GitHub posts (page 1)
showhn

# Jump straight to page 3
showhn --page 2

# Interactively page through all results
showhn --all-pages
```

### Display

Each result shows:

```
  1. Show HN: My Awesome Project
     URL:    https://github.com/user/my-awesome-project
     Points: 312 | 3 hours ago
```

Results are displayed in your system pager (`$PAGER` or `less`).  
Press `q` to quit the pager.

---

## Running Tests

```bash
pip install pytest
pytest
```

## Background

Hacker News' *Show HN* section features many open-source GitHub projects.
The standard search at
[hn.algolia.com](https://hn.algolia.com/?dateRange=all&page=0&prefix=true&query=show%20hn%20github&sort=byDate&type=story)
works but is inconvenient to browse.  
This tool focuses solely on GitHub Show HN posts and provides a clean,
paginated terminal interface.