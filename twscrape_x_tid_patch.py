from __future__ import annotations

import inspect
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

_INSTALLED = False
_LOCK = threading.Lock()

_HOME_URLS = (
    "https://x.com/i/flow/login",
    "https://x.com/home",
)


class _TIDAdapter:
    def __init__(self, ct: Any) -> None:
        self._ct = ct

    def calc(self, method: str, path: str) -> str:
        return self._ct.generate_transaction_id(method=method, path=path)

    @staticmethod
    async def create(
        clt: Any = None,
        *,
        proxy: str | None = None,
        cookies: dict[str, str] | None = None,
        **_: Any,
    ) -> "_TIDAdapter":
        # twscrape >= 0.20 calls create(proxy=..., cookies=...). This fallback
        # builds the generator from the logged-out shell, so both are ignored.
        import asyncio

        return await asyncio.to_thread(_TIDAdapter._create_sync)

    @staticmethod
    def _create_sync() -> "_TIDAdapter":
        import bs4
        import requests
        from x_client_transaction import ClientTransaction
        from x_client_transaction.utils import get_ondemand_file_url

        sess = requests.Session()
        sess.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )

        # The x.com root page no longer carries the "ondemand.s" manifest that
        # get_ondemand_file_url() needs, so handle_x_migration() is not usable here.
        # The logged-out shells below still ship the full manifest.
        last_exc: Exception | None = None
        for url in _HOME_URLS:
            try:
                home = bs4.BeautifulSoup(sess.get(url, timeout=30).content, "html.parser")
                ondemand = sess.get(get_ondemand_file_url(response=home), timeout=30)
                ct = ClientTransaction(home_page_response=home, ondemand_file_response=ondemand)
                return _TIDAdapter(ct)
            except Exception as exc:
                last_exc = exc
                logger.warning("x-tid: cannot build generator from %s: %r", url, exc)

        raise RuntimeError(
            "Cannot build X transaction id from any of "
            + ", ".join(_HOME_URLS)
            + f" (last error: {last_exc!r}). X page layout has probably changed - "
            "update twscrape_x_tid_patch / x_client_transaction."
        )


def _twscrape_has_native_xclid() -> bool:
    """twscrape >= 0.20 ships a maintained, cookie-aware XClIdGen of its own."""
    try:
        from twscrape.xclid import XClIdGen

        return "cookies" in inspect.signature(XClIdGen.create).parameters
    except Exception:
        return False


def is_patch_active() -> bool:
    return _INSTALLED


def install_x_tid_patch() -> bool:
    global _INSTALLED
    with _LOCK:
        if _INSTALLED:
            return False
        if _twscrape_has_native_xclid() and os.getenv("TWS_FORCE_TID_PATCH", "").lower() not in ("1", "true", "yes"):
            logger.info(
                "twscrape provides its own XClIdGen, keeping it "
                "(set TWS_FORCE_TID_PATCH=1 to force the local fallback)"
            )
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
