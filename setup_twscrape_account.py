import asyncio
import os

from twscrape import AccountsPool


async def add_cookie_account(
    db_path: str,
    username: str,
    cookies: str,
    *,
    password: str = "cookie_mode",
    email: str = "cookie_mode@example.com",
    email_password: str = "cookie_mode",
    mfa_code: str | None = None,
) -> bool:
    """Store a cookie-based account, replacing one with the same username."""
    missing = [name for name in ("auth_token", "ct0") if f"{name}=" not in cookies]
    if missing:
        raise ValueError(f"Cookies are missing: {', '.join(missing)}")

    pool = AccountsPool(db_path)
    # add_account() refuses to touch an existing row, so refreshing cookies
    # for a known username means dropping the stale account first.
    await pool.delete_accounts(username)
    await pool.add_account(
        username=username,
        password=password,
        email=email,
        email_password=email_password,
        cookies=cookies,
        mfa_code=mfa_code,
    )
    return any(acc.username == username for acc in await pool.get_all())


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


async def _main() -> int:
    db_path = os.getenv("TWSCRAPE_DB_PATH", "twscrape_accounts.db")
    cookies = os.getenv("TWS_COOKIES", "").strip()
    username = os.getenv("TWS_USERNAME", "cookie_account").strip() or "cookie_account"

    if cookies:
        try:
            added = await add_cookie_account(
                db_path,
                username,
                cookies,
                password=os.getenv("TWS_PASSWORD", "cookie_mode"),
                email=os.getenv("TWS_EMAIL", "cookie_mode@example.com"),
                email_password=os.getenv("TWS_EMAIL_PASSWORD", "cookie_mode"),
                mfa_code=os.getenv("TWS_MFA_CODE") or None,
            )
        except ValueError as exc:
            print(exc)
            return 2
        if not added:
            print(f"Failed to add cookie-based account to {db_path}")
            return 1
        print(f"Cookie-based account added. DB: {db_path}, username: {username}")
        return 0

    try:
        username = _required_env("TWS_USERNAME")
        password = _required_env("TWS_PASSWORD")
        email = _required_env("TWS_EMAIL")
        email_password = _required_env("TWS_EMAIL_PASSWORD")
    except ValueError as exc:
        print(exc)
        print("Expected vars: TWS_USERNAME, TWS_PASSWORD, TWS_EMAIL, TWS_EMAIL_PASSWORD")
        return 2

    pool = AccountsPool(db_path)
    await pool.add_account(
        username=username,
        password=password,
        email=email,
        email_password=email_password,
        mfa_code=os.getenv("TWS_MFA_CODE") or None,
    )

    await pool.login_all(usernames=[username])
    print(f"Account added and login attempted. DB: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
