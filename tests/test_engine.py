import os
import json
import sqlite3
import tempfile
import types

import pytest

from engine import (
    bcolors,
    _get_twscrape_db_path,
    _has_active_twscrape_account,
    _tweet_to_record,
    _save_results,
)


def _make_tweet(
    id=1,
    rawContent="hello",
    date="2026-01-01",
    media=None,
    likeCount=5,
    username="user1",
    location=None,
):
    user = types.SimpleNamespace(username=username, location=location)
    return types.SimpleNamespace(
        id=id,
        rawContent=rawContent,
        date=date,
        media=media,
        user=user,
        likeCount=likeCount,
    )


class TestBcolors:
    def test_ansi_codes_present(self):
        for attr in ("OKGREEN", "OKBLUE", "FAIL", "WARNING", "BOLD", "ENDC"):
            assert "\033[" in getattr(bcolors, attr)


class TestGetDbPath:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("TWSCRAPE_DB_PATH", raising=False)
        assert _get_twscrape_db_path() == "twscrape_accounts.db"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("TWSCRAPE_DB_PATH", "/tmp/custom.db")
        assert _get_twscrape_db_path() == "/tmp/custom.db"


class TestHasActiveAccount:
    def test_missing_file(self):
        assert _has_active_twscrape_account("/nonexistent/path.db") is False

    def test_no_active_account(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE accounts (active INTEGER)")
                conn.execute("INSERT INTO accounts VALUES (0)")
            assert _has_active_twscrape_account(path) is False
        finally:
            os.unlink(path)

    def test_active_account(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE accounts (active INTEGER)")
                conn.execute("INSERT INTO accounts VALUES (1)")
            assert _has_active_twscrape_account(path) is True
        finally:
            os.unlink(path)


class TestTweetToRecord:
    def test_basic_fields(self):
        tweet = _make_tweet(id=42, rawContent="test content", username="testuser", likeCount=10)
        record = _tweet_to_record(tweet)
        assert record["id"] == 42
        assert record["content"] == "test content"
        assert record["user"] == "testuser"
        assert record["likes"] == 10
        assert record["url"] == "https://x.com/testuser/status/42"
        assert record["user_location"] is None

    def test_include_location(self):
        tweet = _make_tweet(username="geo_user", location="Warsaw")
        record = _tweet_to_record(tweet, include_location=True)
        assert record["user_location"] == "Warsaw"

    def test_no_user(self):
        tweet = types.SimpleNamespace(
            id=1, rawContent="x", date="2026-01-01", media=None, user=None, likeCount=0
        )
        record = _tweet_to_record(tweet)
        assert record["user"] is None
        assert record["url"] is None


class TestSaveResults:
    def test_creates_json_and_csv(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "results").mkdir()
        records = [{"id": 1, "content": "hello", "user": "a"}]
        json_path = str(tmp_path / "results" / "out.json")
        csv_path = str(tmp_path / "results" / "out.csv")
        _save_results(records, json_path, csv_path, "saved")
        assert json.loads(open(json_path).read()) == records
        lines = open(csv_path).readlines()
        assert len(lines) == 2
        assert "content" in lines[0]


class TestQidPatterns:
    def test_bundle_regex_matches_real_url(self):
        from twscrape_qids_patch import _BUNDLE_RE

        url = "https://abs.twimg.com/responsive-web/client-web/main.7de7adccd6c7c8f0a.js"
        html = f'<script src="{url}"></script>'
        assert _BUNDLE_RE.findall(html) == [url]

    def test_qid_pattern_extracts_query_id(self):
        from twscrape_qids_patch import _qid_pattern

        js = 'queryId:"hyPfJYJ_XAtDYoslQc-Rgg",operationName:"SearchTimeline"'
        match = _qid_pattern("SearchTimeline").search(js)
        assert match is not None
        assert match.group(1) == "hyPfJYJ_XAtDYoslQc-Rgg"


class TestTidPatch:
    def test_create_sync_reports_clear_error(self, monkeypatch):
        import requests

        from twscrape_x_tid_patch import _TIDAdapter

        def boom(*args, **kwargs):
            raise requests.ConnectionError("offline")

        monkeypatch.setattr(requests.Session, "get", boom)
        with pytest.raises(RuntimeError, match="Cannot build X transaction id"):
            _TIDAdapter._create_sync()


class TestAddCookieAccount:
    def test_stores_and_replaces_account(self, tmp_path):
        import asyncio

        from setup_twscrape_account import add_cookie_account

        db_path = str(tmp_path / "accounts.db")
        assert asyncio.run(add_cookie_account(db_path, "u1", "auth_token=aaa; ct0=bbb"))

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT username, active FROM accounts").fetchall()
        assert rows == [("u1", 1)]

        assert asyncio.run(add_cookie_account(db_path, "u1", "auth_token=ccc; ct0=ddd"))
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT username, cookies FROM accounts").fetchall()
        assert len(rows) == 1
        assert json.loads(rows[0][1])["auth_token"] == "ccc"

    def test_rejects_incomplete_cookies(self, tmp_path):
        import asyncio

        from setup_twscrape_account import add_cookie_account

        with pytest.raises(ValueError, match="ct0"):
            asyncio.run(add_cookie_account(str(tmp_path / "a.db"), "u1", "auth_token=aaa"))
