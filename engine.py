import asyncio
import os
import json
import pandas as pd
import colorama
from anyascii import anyascii
import time 

from twscrape_qids_patch import apply_persisted_qids, refresh_and_apply_sync
from twscrape_x_tid_patch import install_x_tid_patch

colorama.init()

_TWSCRAPE_PREPARED = False


def _prepare_twscrape() -> None:
    global _TWSCRAPE_PREPARED
    if _TWSCRAPE_PREPARED:
        return

    install_x_tid_patch()
    apply_persisted_qids()
    try:
        refresh_and_apply_sync()
    except Exception:
        # Keep old persisted mapping if refresh fails now.
        pass

    _TWSCRAPE_PREPARED = True


def _get_twscrape_db_path() -> str:
    return os.getenv("TWSCRAPE_DB_PATH", "twscrape_accounts.db")


def _has_active_twscrape_account(db_path: str) -> bool:
    if not os.path.exists(db_path):
        return False
    try:
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            active = conn.execute("SELECT COUNT(*) FROM accounts WHERE active=1").fetchone()[0]
        return active > 0
    except Exception:
        return False


def _run_twscrape_search(query: str, limit: int):
    try:
        from twscrape import API
    except Exception:
        return []

    _prepare_twscrape()
    db_path = _get_twscrape_db_path()
    if not _has_active_twscrape_account(db_path):
        return []

    async def _collect():
        api = API(pool=db_path)
        out = []
        async for tweet in api.search(query, limit=limit):
            out.append(tweet)
            if len(out) >= limit:
                break
        return out

    return asyncio.run(_collect())


def _run_twscrape_user(username: str, limit: int):
    try:
        from twscrape import API
    except Exception:
        return []

    _prepare_twscrape()
    db_path = _get_twscrape_db_path()
    if not _has_active_twscrape_account(db_path):
        return []

    async def _collect():
        api = API(pool=db_path)
        out = []
        async for tweet in api.search(f"from:{username}", limit=limit):
            out.append(tweet)
            if len(out) >= limit:
                break
        return out

    return asyncio.run(_collect())


def _can_use_twscrape() -> bool:
    return _has_active_twscrape_account(_get_twscrape_db_path())


def _tweet_to_record(tweet, *, include_location: bool = False) -> dict:
    tweet_user = getattr(tweet, "user", None)
    username = getattr(tweet_user, "username", None)
    tweet_url = f"https://x.com/{username}/status/{tweet.id}" if username else None
    return {
        "id": getattr(tweet, "id", None),
        "content": getattr(tweet, "rawContent", ""),
        "data": str(getattr(tweet, "date", "")),
        "media": str(getattr(tweet, "media", None)),
        "user": username,
        "user_location": getattr(tweet_user, "location", None) if include_location else None,
        "url": tweet_url,
        "likes": getattr(tweet, "likeCount", None),
    }


def _save_results(records: list[dict], json_path: str, csv_path: str, success_message: str) -> None:
    os.makedirs("results", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as file_handle:
        json.dump(records, file_handle, ensure_ascii=False)

    with open(json_path, "r", encoding="utf-8") as file_handle:
        data = json.loads(file_handle.read())

    df = pd.json_normalize(data)
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(bcolors.BOLD + bcolors.WARNING + success_message + bcolors.ENDC)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
class scrapeer:
    def selfCheck():
        print(bcolors.BOLD + bcolors.OKBLUE + "\nRunning environment check..." + bcolors.ENDC)
        db_path = _get_twscrape_db_path()
        active = _has_active_twscrape_account(db_path)

        print(f"[1/3] twscrape DB path: {db_path}")
        print(f"[2/3] active account available: {active}")

        if not active:
            print(
                bcolors.BOLD
                + bcolors.FAIL
                + "No active twscrape account found. Run setup_twscrape_account.py first."
                + bcolors.ENDC
            )
            return

        search_rows = _run_twscrape_search("python lang:en", 2)
        user_rows = _run_twscrape_user("nasa", 2)

        print(f"[3/3] search test rows: {len(search_rows)} | user test rows: {len(user_rows)}")

        if search_rows and user_rows:
            print(bcolors.BOLD + bcolors.OKGREEN + "Environment check passed." + bcolors.ENDC)
        else:
            print(bcolors.BOLD + bcolors.WARNING + "Environment check partial: one of test queries returned 0 rows." + bcolors.ENDC)

    def twitterUser():
        choose1 = str(input(bcolors.BOLD + bcolors.OKBLUE + "Enter the username, without the @ sign and without spaces:" + bcolors.ENDC))
        while not choose1.strip():
            choose1 = str(input(bcolors.BOLD + bcolors.OKBLUE + "Enter the username, without the @ sign and without spaces:" + bcolors.ENDC))
        choose2 = choose1.replace(" ", "")
        choose = anyascii(choose2)

        while True:
            try:
                m = int(input(bcolors.BOLD + bcolors.OKBLUE + "Enter how many tweets to display:" + bcolors.ENDC))
                n = int(m)
                if n > 0:
                    break
                else:
                    print(
                        bcolors.BOLD + bcolors.FAIL + "\n The digit must be greater than 0\n" + bcolors.ENDC)
                    continue
            except ValueError:
                print(bcolors.BOLD + bcolors.WARNING + "\n You need to enter a number, please try again \n" + bcolors.ENDC)
                continue
        tweets = []

        if not _can_use_twscrape():
            db_path = _get_twscrape_db_path()
            print(
                bcolors.BOLD
                + bcolors.FAIL
                + f"\nNo active twscrape account found. Check DB: {db_path}\n"
                + bcolors.ENDC
            )
            return

        try:
            tw_items = _run_twscrape_user(choose, n)
            for i, tweet in enumerate(tw_items):
                record = _tweet_to_record(tweet)
                tweets.append(record)
                print(f"{i} content: {record['content']}, data: {record['data']}")
        except Exception as exc:
            print(bcolors.BOLD + bcolors.WARNING + f"\nScraping failed ({exc}).\n" + bcolors.ENDC)
            return

        if not tweets:
            print(bcolors.BOLD + bcolors.FAIL + "\nNo results returned by twscrape.\n" + bcolors.ENDC)
            return
                        
        timer = time.strftime("%Y%m%d-%H%M%S")
        json_path = f"results/tweets_user_{choose}_{timer}.json"
        csv_path = f"results/tweets_user_{choose}_{timer}.csv"

        _save_results(
            tweets,
            json_path,
            csv_path,
            f"\nThe results were saved to the results folder in the tweets_user_{choose}_{timer}.json and tweets_user_{choose}_{timer}.csv files",
        )


    def twitterSearch():
        choose = str(input(bcolors.BOLD + bcolors.OKGREEN + "Enter search data: " + bcolors.ENDC))
        while not choose.strip():
            choose = str(input(bcolors.BOLD + bcolors.OKGREEN + "Enter search data: ` " + bcolors.ENDC))

        while True:
            try:
                m = int(input(bcolors.BOLD + bcolors.OKBLUE + "Enter how many tweets to display: " + bcolors.ENDC))
                n = int(m)
                if n > 0:
                    break
                else:
                    print(
                        bcolors.BOLD + bcolors.FAIL + "\n The digit must be greater than 0\n" + bcolors.ENDC)
                    continue
            except ValueError:
                print(bcolors.BOLD + bcolors.WARNING + "\n You need to enter a number, please try again \n" + bcolors.ENDC)
                continue
        tweets = []

        if not _can_use_twscrape():
            db_path = _get_twscrape_db_path()
            print(
                bcolors.BOLD
                + bcolors.FAIL
                + f"\nNo active twscrape account found. Check DB: {db_path}\n"
                + bcolors.ENDC
            )
            return

        try:
            tw_items = _run_twscrape_search(choose, n)
            for i, tweet in enumerate(tw_items):
                record = _tweet_to_record(tweet)
                tweets.append(record)
                print(f"{i} content: {record['content']}, user: {record['user']}, data: {record['data']}")
        except Exception as exc:
            print(bcolors.BOLD + bcolors.WARNING + f"\nScraping failed ({exc}).\n" + bcolors.ENDC)
            return

        if not tweets:
            print(bcolors.BOLD + bcolors.FAIL + "\nNo results returned by twscrape.\n" + bcolors.ENDC)
            return
                        
        timer = time.strftime("%Y%m%d-%H%M%S")
        json_path = f"results/tweets_search_{timer}.json"
        csv_path = f"results/tweets_search_{timer}.csv"

        _save_results(
            tweets,
            json_path,
            csv_path,
            f"\nThe results were saved to the results folder in the tweets_search_{timer}.json and tweets_search_{timer}.csv files\n",
        )