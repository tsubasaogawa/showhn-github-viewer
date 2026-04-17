# Development Guide

## Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)

## Setup

```bash
# Install dependencies and setup venv
uv sync
```

## Running the Application

```bash
# Run the TUI
uv run main

# Run with startup filter and item count
uv run main --filter 10 --num 50
```

## Testing

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v
```

## Project Structure

 - `src/`: Main application logic and TUI implementation.
- `tests/`: Project test suite.
- `pyproject.toml`: Project metadata and dependencies.
