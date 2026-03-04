"""Tests for showhn.py."""

import time
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

import showhn
from showhn import (
    build_page_content,
    fetch_stories,
    format_story,
    format_time_ago,
    main,
)


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
        with patch("showhn.requests.get") as mock_get:
            mock_get.return_value = self._mock_response({"hits": [], "nbPages": 0})
            fetch_stories(page=2)
            url = mock_get.call_args[0][0]
            _, kwargs = mock_get.call_args
            params = kwargs.get("params") or mock_get.call_args[0][1]
            assert url == showhn.API_URL
            assert params["query"] == "show hn github"
            assert params["page"] == 2
            assert params["tags"] == "story"

    def test_returns_json(self):
        payload = {"hits": [{"title": "test"}], "nbPages": 1}
        with patch("showhn.requests.get") as mock_get:
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
        with patch("showhn.fetch_stories", return_value=fake_data), patch(
            "showhn.run_tui"
        ) as mock_tui:
            result = runner.invoke(main, [])
        assert result.exit_code == 0
        mock_tui.assert_called_once_with(initial_page=0, initial_data=fake_data)

    def test_page_option(self):
        runner = CliRunner()
        fake_data = self._fake_data()
        with patch("showhn.fetch_stories", return_value=fake_data) as mock_fetch, patch(
            "showhn.run_tui"
        ) as mock_tui:
            runner.invoke(main, ["--page", "3"])
            mock_fetch.assert_called_once_with(page=3)
            mock_tui.assert_called_once_with(initial_page=3, initial_data=fake_data)

    def test_no_results(self):
        runner = CliRunner()
        with patch("showhn.fetch_stories", return_value={"hits": [], "nbPages": 0}), patch(
            "showhn.run_tui"
        ) as mock_tui:
            result = runner.invoke(main, [])
        assert result.exit_code == 0
        mock_tui.assert_not_called()

    def test_request_error(self):
        runner = CliRunner()
        with patch(
            "showhn.fetch_stories",
            side_effect=showhn.requests.RequestException("timeout"),
        ):
            result = runner.invoke(main, [])
        assert result.exit_code != 0
