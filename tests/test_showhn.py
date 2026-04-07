"""Tests for src package."""
import sys
from unittest.mock import MagicMock, patch

# Mock curses before src is imported
mock_curses = MagicMock()
sys.modules["curses"] = mock_curses

import time
import pytest
from click.testing import CliRunner

import src
from src import (
    build_page_content,
    fetch_stories,
    format_story,
    format_time_ago,
    is_github_url,
    main,
)


# ---------------------------------------------------------------------------
# is_github_url
# ---------------------------------------------------------------------------

class TestIsGitHubUrl:
    def test_github_https(self):
        assert is_github_url("https://github.com/user/repo") is True

    def test_github_http(self):
        assert is_github_url("http://github.com/user/repo") is True

    def test_github_no_path(self):
        assert is_github_url("https://github.com") is True

    def test_not_github(self):
        assert is_github_url("https://gitlab.com/user/repo") is False

    def test_none(self):
        assert is_github_url(None) is False

    def test_empty(self):
        assert is_github_url("") is False

    def test_invalid_url(self):
        # urlparse might handle this weirdly but it shouldn't be github.com
        assert is_github_url("not a url") is False


# ---------------------------------------------------------------------------
# format_time_ago
# ---------------------------------------------------------------------------

class TestFormatTimeAgo:
    def _now(self):
        return int(time.time())

    def test_seconds(self):
        assert format_time_ago(self._now() - 30) == "30 seconds ago"

    def test_one_second(self):
        assert format_time_ago(self._now() - 1) == "1 second ago"

    def test_one_minute(self):
        assert format_time_ago(self._now() - 60) == "1 minute ago"

    def test_minutes(self):
        assert format_time_ago(self._now() - 300) == "5 minutes ago"

    def test_one_hour(self):
        assert format_time_ago(self._now() - 3600) == "1 hour ago"

    def test_hours(self):
        assert format_time_ago(self._now() - 7200) == "2 hours ago"

    def test_days(self):
        assert format_time_ago(self._now() - 86400 * 3) == "3 days ago"

    def test_one_day(self):
        assert format_time_ago(self._now() - 86400) == "1 day ago"

    def test_months(self):
        assert format_time_ago(self._now() - 86400 * 60) == "2 months ago"

    def test_years(self):
        assert format_time_ago(self._now() - 86400 * 400) == "1 year ago"


# ---------------------------------------------------------------------------
# format_story
# ---------------------------------------------------------------------------

class TestFormatStory:
    def _make_story(self, **kwargs):
        defaults = {
            "title": "Show HN: My Cool Project",
            "url": "https://github.com/user/repo",
            "points": 42,
            "created_at_i": int(time.time()) - 3600,
        }
        defaults.update(kwargs)
        return defaults

    def test_contains_title(self):
        output = format_story(1, self._make_story())
        assert "Show HN: My Cool Project" in output

    def test_contains_url(self):
        output = format_story(1, self._make_story())
        assert "https://github.com/user/repo" in output

    def test_contains_points(self):
        output = format_story(1, self._make_story())
        assert "42" in output

    def test_contains_time_ago(self):
        output = format_story(1, self._make_story())
        assert "ago" in output

    def test_index_shown(self):
        output = format_story(7, self._make_story())
        assert "7." in output

    def test_missing_url_fallback(self):
        output = format_story(1, self._make_story(url=None))
        assert "(no URL)" in output

    def test_missing_points_fallback(self):
        output = format_story(1, self._make_story(points=None))
        assert "0" in output


# ---------------------------------------------------------------------------
# build_page_content
# ---------------------------------------------------------------------------

class TestBuildPageContent:
    def _hits(self, n=3):
        now = int(time.time())
        return [
            {
                "title": f"Story {i}",
                "url": f"https://github.com/user/repo{i}",
                "points": i * 10,
                "created_at_i": now - i * 60,
            }
            for i in range(1, n + 1)
        ]

    def test_header_shows_page_number(self):
        content = build_page_content(self._hits(), page=0, num_pages=3)
        assert "Page 1 / 3" in content

    def test_footer_shown(self):
        content = build_page_content(self._hits(), page=0, num_pages=1)
        assert "End of page 1" in content

    def test_navigation_hint_when_more_pages(self):
        content = build_page_content(self._hits(), page=0, num_pages=5)
        assert "--page" in content

    def test_no_navigation_hint_on_last_page(self):
        content = build_page_content(self._hits(), page=4, num_pages=5)
        assert "--page" not in content

    def test_all_stories_included(self):
        hits = self._hits(n=5)
        content = build_page_content(hits, page=0, num_pages=1)
        for h in hits:
            assert h["title"] in content


# ---------------------------------------------------------------------------
# fetch_stories (mocked HTTP)
# ---------------------------------------------------------------------------

class TestFetchStories:
    def _mock_response(self, payload):
        mock_resp = MagicMock()
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    def test_correct_query_params(self):
        with patch("src.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({"hits": [], "nbPages": 0})
            fetch_stories(page=2)
            url = mock_get.call_args[0][0]
            _, kwargs = mock_get.call_args
            params = kwargs.get("params") or mock_get.call_args[0][1]
            assert url == src.API_URL
            assert params["query"] == "show hn github"
            assert params["page"] == 2
            assert params["tags"] == "story"

    def test_returns_json(self):
        payload = {"hits": [{"title": "test"}], "nbPages": 1}
        with patch("src.requests.get") as mock_get:
            mock_get.return_value = self._mock_response(payload)
            result = fetch_stories()
            assert result == payload


# ---------------------------------------------------------------------------
# CLI integration (Click test runner)
# ---------------------------------------------------------------------------

class TestCLI:
    def _fake_data(self):
        now = int(time.time())
        return {
            "hits": [
                {
                    "title": "Show HN: TestRepo",
                    "url": "https://github.com/user/testrepo",
                    "points": 99,
                    "created_at_i": now - 120,
                }
            ],
            "nbPages": 1,
        }

    def test_default_run(self):
        runner = CliRunner()
        fake_data = self._fake_data()
        with patch("src.fetch_stories", return_value=fake_data), patch(
            "src.run_tui"
        ) as mock_tui:
            result = runner.invoke(main, [])
        assert result.exit_code == 0
        mock_tui.assert_called_once_with(initial_page=0, initial_data=fake_data)

    def test_page_option(self):
        runner = CliRunner()
        fake_data = self._fake_data()
        with patch("src.fetch_stories", return_value=fake_data) as mock_fetch, patch(
            "src.run_tui"
        ) as mock_tui:
            runner.invoke(main, ["--page", "3"])
            mock_fetch.assert_called_once_with(page=3)
            mock_tui.assert_called_once_with(initial_page=3, initial_data=fake_data)

    def test_no_results(self):
        runner = CliRunner()
        with patch("src.fetch_stories", return_value={"hits": [], "nbPages": 0}), patch(
            "src.run_tui"
        ) as mock_tui:
            result = runner.invoke(main, [])
        assert result.exit_code == 0
        mock_tui.assert_not_called()

    def test_filtering_non_github_urls(self):
        runner = CliRunner()
        fake_data = {
            "hits": [
                {"title": "GitHub", "url": "https://github.com/a/b"},
                {"title": "Not GitHub", "url": "https://example.com"},
            ],
            "nbPages": 1,
        }
        filtered_data = {
            "hits": [{"title": "GitHub", "url": "https://github.com/a/b"}],
            "nbPages": 1,
        }
        with patch("src.fetch_stories", return_value=fake_data), patch(
            "src.run_tui"
        ) as mock_tui:
            runner.invoke(main, [])
        
        # Verify run_tui called with filtered hits
        # Note: we need to check the call args correctly
        _, kwargs = mock_tui.call_args
        assert len(kwargs["initial_data"]["hits"]) == 1
        assert kwargs["initial_data"]["hits"][0]["title"] == "GitHub"

    def test_request_error(self):
        runner = CliRunner()
        with patch(
            "src.fetch_stories",
            side_effect=src.requests.RequestException("timeout"),
        ):
            result = runner.invoke(main, [])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# TUI Drawing
# ---------------------------------------------------------------------------

class TestTUIDrawing:
    def test_draw_tui_uses_full_height(self, mocker):
        from src import draw_tui
        stdscr = MagicMock()
        # Mock window size 10x40
        stdscr.getmaxyx.return_value = (10, 40)
        
        hits = [{"title": f"Story {i}"} for i in range(20)]
        
        # We need to mock _safe_addnstr because it uses curses constants
        with patch("src._safe_addnstr") as mock_addnstr:
            draw_tui(stdscr, hits, selected_idx=0, page=0, num_pages=1)
            
            # Header at 0, Footer at height-1 (9)
            # List items should be drawn from row 1 to 8
            # Total 8 rows for list items
            list_calls = [c for c in mock_addnstr.call_args_list if 1 <= c.args[1] <= 8]
            assert len(list_calls) == 8
            
            # Verify padding for selected item
            # The first item (idx 0) is selected
            selected_call = [c for c in list_calls if c.args[1] == 1][0]
            drawn_text = selected_call.args[3]
            assert len(drawn_text) == 40
            assert drawn_text.startswith("  1. Story 0")
            assert drawn_text.endswith(" ")

    def test_draw_tui_fills_split_panes_across_full_area(self):
        from src import draw_tui

        stdscr = MagicMock()
        stdscr.getmaxyx.return_value = (6, 20)

        hits = [{"title": "Story 0", "url": "https://github.com/user/repo"}]
        readme_lines = ["README"]

        with patch("src._safe_addnstr") as mock_addnstr:
            draw_tui(
                stdscr,
                hits,
                selected_idx=0,
                page=0,
                num_pages=1,
                readme_lines=readme_lines,
            )

            list_calls = [
                c for c in mock_addnstr.call_args_list if 1 <= c.args[1] <= 4 and c.args[2] == 0
            ]
            divider_calls = [
                c for c in mock_addnstr.call_args_list if 1 <= c.args[1] <= 4 and c.args[2] == 9
            ]
            readme_calls = [
                c for c in mock_addnstr.call_args_list if 1 <= c.args[1] <= 4 and c.args[2] == 10
            ]

            assert len(list_calls) == 4
            assert len(divider_calls) == 4
            assert len(readme_calls) == 4
            assert all(c.args[4] == 9 for c in list_calls)
            assert all(c.args[4] == 1 for c in divider_calls)
            assert all(c.args[4] == 10 for c in readme_calls)
            assert divider_calls[0].args[3] == "|"
            assert readme_calls[0].args[3].startswith("README")
            assert len(readme_calls[0].args[3]) == 10
