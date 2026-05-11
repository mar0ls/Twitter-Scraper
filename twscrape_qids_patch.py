from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TRACKED_OPS: tuple[str, ...] = (
    "SearchTimeline",
    "UserByScreenName",
    "UserByRestId",
    "TweetDetail",
    "UserTweets",
    "UserTweetsAndReplies",
    "ListLatestTweetsTimeline",
    "Followers",
    "Following",
    "BlueVerifiedFollowers",
    "UserCreatorSubscriptions",
    "UserMedia",
    "GenericTimelineById",
)

_BUNDLE_RE = re.compile(r"https://abs\\.twimg\\.com/responsive-web/client-web[^\"']+\\.js")
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_STORE_PATH = Path(__file__).parent / "results" / "twscrape_qids.json"


def _qid_pattern(op: str) -> re.Pattern[str]:
    return re.compile(rf'queryId:"([A-Za-z0-9_-]+)",operationName:"{op}"')


async def fetch_current_qids(timeout: float = 30.0) -> dict[str, str]:
    headers = {"user-agent": _USER_AGENT}
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as cli:
        rep = await cli.get("https://x.com/i/flow/login")
        rep.raise_for_status()
        bundles = list(dict.fromkeys(_BUNDLE_RE.findall(rep.text)))
        if not bundles:
            raise RuntimeError("No JS bundles found on x.com")

        result: dict[str, str] = {}
        for url in bundles:
            if all(op in result for op in TRACKED_OPS):
                break
            try:
                body = (await cli.get(url)).text
            except Exception as exc:
                logger.warning("Bundle fetch failed %s: %s", url, exc)
                continue
            for op in TRACKED_OPS:
                if op in result:
                    continue
                m = _qid_pattern(op).search(body)
                if m:
                    result[op] = m.group(1)
        return result


def _store_load() -> dict[str, Any]:
    if not _STORE_PATH.exists():
        return {}
    try:
        return json.loads(_STORE_PATH.read_text("utf-8"))
    except Exception as exc:
        logger.warning("Cannot read %s: %s", _STORE_PATH, exc)
        return {}


def _store_save(payload: dict[str, Any]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _apply_to_twscrape(qids: dict[str, str]) -> dict[str, str]:
    try:
        from twscrape import api as tw_api
    except Exception as exc:
        logger.warning("twscrape unavailable, skipping qid patch: %s", exc)
        return {}

    diff: dict[str, str] = {}
    for op, qid in qids.items():
        attr = f"OP_{op}"
        old = getattr(tw_api, attr, None)
        new = f"{qid}/{op}"
        if old != new:
            setattr(tw_api, attr, new)
            diff[op] = old or ""
    return diff


def apply_persisted_qids() -> dict[str, str]:
    payload = _store_load()
    qids = {k: v for k, v in payload.get("qids", {}).items() if k in TRACKED_OPS}
    if not qids:
        return {}
    return _apply_to_twscrape(qids)


async def refresh_and_apply() -> dict[str, Any]:
    qids = await fetch_current_qids()
    missing = [op for op in TRACKED_OPS if op not in qids]
    applied = _apply_to_twscrape(qids)
    payload = {
        "qids": qids,
        "missing": missing,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _store_save(payload)
    return {**payload, "applied": applied}


def refresh_and_apply_sync() -> dict[str, Any]:
    return asyncio.run(refresh_and_apply())
