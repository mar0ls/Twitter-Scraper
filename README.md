<div id="header" align="center">
    <img src="https://media3.giphy.com/media/MNa0HKdhc3SGQ/giphy.webp?cid=6c09b9526ec6b64b07d26580f637063fe326684a800475f9&rid=giphy.webp&ct=g" width="100"/>
</div>

# Twitter-Scraper

[![CI](https://github.com/mar0ls/Twitter-Scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/mar0ls/Twitter-Scraper/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)

> **Verified working — May 11, 2026**

Command-line Twitter/X scraper with two interactive modes:

- keyword / hashtag search
- search by username

Results are saved to the [results](results) directory as JSON and CSV files.

## How it works

The scraper uses `twscrape` for search and user queries, extended by two local patch modules:

- `twscrape_qids_patch` — refreshes GraphQL query IDs from X bundles and caches them in `results/twscrape_qids.json`
- `twscrape_x_tid_patch` — replaces twscrape's transaction-ID generator with `XClientTransaction`

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Menu:

1. Tweet search
2. Search by username
3. Help
4. Exit
5. Environment check

## Account setup

`twscrape` needs at least one active account. Fresh clones do not include a database or session cookies.

### Password-based

```bash
export TWS_USERNAME='your_x_username'
export TWS_PASSWORD='your_x_password'
export TWS_EMAIL='your_email_used_on_x'
export TWS_EMAIL_PASSWORD='your_email_password'
# export TWS_MFA_CODE='123456'

python setup_twscrape_account.py
```

### Cookie-based

```bash
export TWS_USERNAME='cookie_account'
export TWS_COOKIES='auth_token=...; ct0=...'
python setup_twscrape_account.py
```

Default database path: `twscrape_accounts.db`. Override with:

```bash
export TWSCRAPE_DB_PATH='twscrape_accounts.db'
```

## Output fields

| Field | Description |
|---|---|
| `id` | Tweet ID |
| `content` | Tweet text |
| `data` | Timestamp |
| `media` | Attached media |
| `user` | Username |
| `user_location` | Profile location (user search only) |
| `url` | Direct link to tweet |
| `likes` | Like count |

## Environment check

Option `5` verifies:

- configured database path
- presence of an active account
- a keyword search test (2 tweets)
- a user search test (2 tweets)

## Advanced search operators

Full reference: <https://github.com/igorbrigadir/twitter-advanced-search>

Selected operators:

| Operator | Example |
|---|---|
| hashtag | `#strozyk` |
| exclude word | `-word` |
| language | `lang:pl` |
| from user | `from:nasa` |
| date range | `since:2024-01-01 until:2024-12-31` |
| verified | `filter:blue_verified` |
| geo | `near:Warsaw` / `geocode:52.23,21.01,10km` |

## Licenses

| Package | License |
|---|---|
| twscrape | MIT |
| XClientTransaction | MIT |
| anyascii | MIT |
| pandas | BSD 3-Clause |
| requests | Apache-2.0 |
| colorama | BSD |
| pytest | MIT |

The repository does not vendor any third-party source files. Before redistribution, review the license terms of all installed dependencies.
