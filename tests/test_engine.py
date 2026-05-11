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
