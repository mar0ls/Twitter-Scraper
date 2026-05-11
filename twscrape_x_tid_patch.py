from __future__ import annotations

import logging
import threading
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_INSTALLED = False
_LOCK = threading.Lock()


class _TIDAdapter:
    def __init__(self, ct: Any) -> None:
        self._ct = ct

    def calc(self, method: str, path: str) -> str:
        return self._ct.generate_transaction_id(method=method, path=path)

    @staticmethod
    async def create(clt: httpx.AsyncClient | None = None) -> "_TIDAdapter":
        import asyncio

        return await asyncio.to_thread(_TIDAdapter._create_sync)

    @staticmethod
    def _create_sync() -> "_TIDAdapter":
        import requests
        from x_client_transaction import ClientTransaction
        from x_client_transaction.utils import get_ondemand_file_url, handle_x_migration

        sess = requests.Session()
        sess.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        home = handle_x_migration(sess)
        ondemand = sess.get(get_ondemand_file_url(response=home), timeout=30)
        ct = ClientTransaction(home_page_response=home, ondemand_file_response=ondemand)
        return _TIDAdapter(ct)


def install_x_tid_patch() -> bool:
    global _INSTALLED
    with _LOCK:
        if _INSTALLED:
            return False
        try:
            from twscrape import queue_client as tw_qc
            from twscrape import xclid as tw_xclid
        except Exception as exc:
            logger.warning("twscrape unavailable, skipping x-tid patch: %s", exc)
            return False

        tw_xclid.XClIdGen = _TIDAdapter  # type: ignore[assignment]
        tw_qc.XClIdGen = _TIDAdapter  # type: ignore[assignment]
        try:
            tw_qc.XClIdGenStore.items.clear()  # type: ignore[attr-defined]
        except Exception:
            pass

        _INSTALLED = True
        logger.info("Installed twscrape x-tid patch")
        return True
