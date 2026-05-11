import asyncio
import os

from twscrape import AccountsPool


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
        pool = AccountsPool(db_path)
        await pool.add_account(
            username=username,
            password=os.getenv("TWS_PASSWORD", "cookie_mode"),
            email=os.getenv("TWS_EMAIL", "cookie_mode@example.com"),
            email_password=os.getenv("TWS_EMAIL_PASSWORD", "cookie_mode"),
            cookies=cookies,
            mfa_code=os.getenv("TWS_MFA_CODE") or None,
        )
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
