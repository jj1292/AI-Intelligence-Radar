"""Collect T2 X signals through a locally authenticated twscrape account."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
import re
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.collection import CollectionBatch


STATE_DIR_ENV = "RADAR_STATE_DIR"
ACCOUNT_DB_ENV = "X_TWSCRAPE_DB"
ACCOUNT_USERNAME_ENV = "X_ACCOUNT_USERNAME"
AUTH_TOKEN_ENV = "X_COOKIE_AUTH_TOKEN"
CSRF_TOKEN_ENV = "X_COOKIE_CT0"
DEFAULT_STATE_DIR = Path.home() / ".ai-intelligence-radar"
AsyncTweetFetcher = Callable[[str, Path, int], Awaitable[list[Any]]]


def resolve_state_dir(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    return Path(env.get(STATE_DIR_ENV, str(DEFAULT_STATE_DIR))).expanduser()


def resolve_account_db(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    configured = env.get(ACCOUNT_DB_ENV)
    return Path(configured).expanduser() if configured else resolve_state_dir(env) / "twscrape.db"


def resolve_checkpoint_path(
    source_id: str,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return resolve_state_dir(environ) / "checkpoints" / f"{source_id}.json"


def setup_values_from_env(environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    env = os.environ if environ is None else environ
    username = env.get(ACCOUNT_USERNAME_ENV, "").strip().lstrip("@")
    auth_token = env.get(AUTH_TOKEN_ENV, "").strip()
    csrf_token = env.get(CSRF_TOKEN_ENV, "").strip()
    missing = [
        name
        for name, value in (
            (ACCOUNT_USERNAME_ENV, username),
            (AUTH_TOKEN_ENV, auth_token),
            (CSRF_TOKEN_ENV, csrf_token),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing X publisher settings: {', '.join(missing)}")
    return username, f"auth_token={auth_token}; ct0={csrf_token}"


def load_since_id(path: Path) -> int | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get("since_id")
    if value is None:
        return None
    text = str(value)
    if not text.isdigit():
        raise ValueError(f"Invalid X checkpoint: {path}")
    return int(text)


def save_since_id(path: Path, since_id: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps({"since_id": str(since_id)}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    temporary.replace(path)


def _compact_text(value: str, limit: int) -> str:
    return re.sub(r"\s+", " ", value).strip()[:limit].rstrip()


def _tweet_id(tweet: Any) -> int | None:
    value = getattr(tweet, "id_str", None) or getattr(tweet, "id", None)
    text = str(value) if value is not None else ""
    return int(text) if text.isdigit() else None


def _author_company(username: str, source: dict[str, Any]) -> str:
    author_companies = source.get("author_companies", {})
    normalized = username.casefold()
    for handle, company in author_companies.items():
        if handle.casefold() == normalized:
            return str(company)
    return str(source["company"])


def normalize_x_tweet(
    tweet: Any,
    source: dict[str, Any],
    *,
    retrieved_at: datetime | None = None,
) -> dict[str, Any] | None:
    tweet_id = _tweet_id(tweet)
    user = getattr(tweet, "user", None)
    username = str(getattr(user, "username", "")).strip()
    content = _compact_text(str(getattr(tweet, "rawContent", "")), 400)
    url = str(getattr(tweet, "url", "")).strip()
    published_at = getattr(tweet, "date", None)
    if tweet_id is None or not username or not content or not url or not isinstance(published_at, datetime):
        return None
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    headline = _compact_text(content, 96)
    company = _author_company(username, source)
    retrieved = retrieved_at or datetime.now(timezone.utc)
    return {
        "title": f"{company} · @{username}: {headline}",
        "canonical_url": url,
        "source_name": source["name"],
        "source_tier": source["source_tier"],
        "platform": "x",
        "company": company,
        "author": f"@{username}",
        "published_at": published_at.isoformat(),
        "retrieved_at": retrieved.isoformat(),
        "summary": content,
        "why_it_matters": (
            "这是官方或核心团队 X 账号的一手表达，可用于发现发布背景与传播信号；"
            "产品能力事实仍需 T1 官方来源交叉验证。"
        ),
        "evidence": [content[:240].rstrip()],
        "topics": list(source["topics"]),
        "impact_score": 3,
        "confidence": 0.85,
        "external_id": str(tweet_id),
    }


async def fetch_tweets_with_twscrape(query: str, account_db: Path, limit: int) -> list[Any]:
    if not account_db.exists():
        raise RuntimeError(
            "X account is not configured. Run `python3 -m tools.x_twscrape setup <username>`."
        )
    os.environ.setdefault("TWS_TELEMETRY", "0")
    try:
        from twscrape import API
        from twscrape.accounts_pool import NoAccountError
    except ImportError as exc:
        raise RuntimeError("twscrape is not installed. Install requirements.txt first.") from exc

    api = API(
        str(account_db),
        raise_when_no_account=True,
        wait_timeout=30,
        wait_interval=1,
    )
    stats = await api.pool.stats()
    if int(stats.get("active", 0)) < 1:
        raise RuntimeError("No active X account is available in the local account database.")
    try:
        return [tweet async for tweet in api.search(query, limit=limit)]
    except NoAccountError as exc:
        raise RuntimeError("No X account is currently available; it may be rate-limited.") from exc
    except Exception as exc:
        raise RuntimeError(f"X collection failed ({type(exc).__name__}).") from exc


async def collect_x_posts_async(
    source: dict[str, Any],
    *,
    fetcher: AsyncTweetFetcher = fetch_tweets_with_twscrape,
    account_db: Path | None = None,
    checkpoint_path: Path | None = None,
    retrieved_at: datetime | None = None,
) -> CollectionBatch:
    if source.get("collection_mode") != "x_twscrape":
        raise ValueError(f"Source {source.get('id')} is not a twscrape source.")
    query = str(source.get("query", "")).strip()
    if not query:
        raise ValueError(f"Source {source.get('id')} has no X search query.")

    limit = int(source.get("max_results", 100))
    if limit < 1 or limit > 500:
        raise ValueError("X max_results must be between 1 and 500.")
    database = account_db or resolve_account_db()
    checkpoint = checkpoint_path or resolve_checkpoint_path(source["id"])
    previous_since_id = load_since_id(checkpoint)
    tweets = await fetcher(query, database, limit)

    signals: list[dict[str, Any]] = []
    newest_id = previous_since_id
    for tweet in tweets:
        tweet_id = _tweet_id(tweet)
        if tweet_id is None:
            continue
        if previous_since_id is not None and tweet_id <= previous_since_id:
            continue
        signal = normalize_x_tweet(tweet, source, retrieved_at=retrieved_at)
        if signal is None:
            continue
        signals.append(signal)
        newest_id = tweet_id if newest_id is None else max(newest_id, tweet_id)

    commit = None
    if newest_id is not None and newest_id != previous_since_id:
        commit = lambda: save_since_id(checkpoint, newest_id)
    return CollectionBatch(signals=signals, commit_checkpoint=commit)


def collect_x_posts(source: dict[str, Any]) -> CollectionBatch:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(collect_x_posts_async(source))
    raise RuntimeError("The synchronous X collector cannot run inside an active event loop.")


async def _setup_account(
    username: str,
    account_db: Path,
    cookies: str,
    *,
    replace: bool = False,
) -> bool:
    os.environ.setdefault("TWS_TELEMETRY", "0")
    try:
        from twscrape import API
    except ImportError as exc:
        raise RuntimeError("twscrape is not installed. Install requirements.txt first.") from exc

    account_db.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    api = API(str(account_db), raise_when_no_account=True)
    existing = await api.pool.get_account(username)
    if existing is not None:
        if not replace:
            raise RuntimeError(
                f"X account @{username} already exists. Use setup --replace to refresh its cookies."
            )
        await api.pool.delete_accounts(username)
    await api.pool.add_account_cookies(username, cookies)
    accounts = await api.pool.accounts_info()
    try:
        account_db.chmod(0o600)
    except OSError:
        pass
    return any(account["username"] == username and account["active"] for account in accounts)


async def _account_status(account_db: Path) -> list[dict[str, Any]]:
    if not account_db.exists():
        return []
    try:
        from twscrape import API
    except ImportError as exc:
        raise RuntimeError("twscrape is not installed. Install requirements.txt first.") from exc
    return await API(str(account_db)).pool.accounts_info()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the local X account used by Radar.")
    parser.add_argument("--db", type=Path, default=resolve_account_db())
    subparsers = parser.add_subparsers(dest="command", required=True)
    setup = subparsers.add_parser("setup", help="Add an X account from browser cookies")
    setup.add_argument("username", help="X username without @")
    setup.add_argument(
        "--replace",
        action="store_true",
        help="Replace cookies for an account that is already configured",
    )
    subparsers.add_parser(
        "setup-env",
        help="Configure the publisher account from CI environment variables",
    )
    subparsers.add_parser("status", help="Show account status without exposing cookies")
    subparsers.add_parser("paths", help="Show local state paths")
    args = parser.parse_args()
    account_db = args.db.expanduser()

    if args.command == "paths":
        print(f"account_db={account_db}")
        print(f"checkpoint_dir={resolve_state_dir() / 'checkpoints'}")
        return
    if args.command == "setup":
        cookies = getpass.getpass("Paste auth_token=...; ct0=... (input is hidden): ")
        if "auth_token=" not in cookies or "ct0=" not in cookies:
            raise SystemExit("Both auth_token and ct0 are required.")
        active = asyncio.run(
            _setup_account(args.username, account_db, cookies, replace=args.replace)
        )
        if not active:
            raise SystemExit("The account was stored but is not active. Check the cookie values.")
        print(
            f"X account @{args.username} is stored and enabled in {account_db}. "
            "Run an X collection to verify the cookies online."
        )
        return

    if args.command == "setup-env":
        try:
            username, cookies = setup_values_from_env()
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        active = asyncio.run(_setup_account(username, account_db, cookies, replace=True))
        if not active:
            raise SystemExit("The X publisher account was stored but is not enabled.")
        print(f"X publisher account @{username} is stored and enabled in {account_db}.")
        return

    accounts = asyncio.run(_account_status(account_db))
    if not accounts:
        raise SystemExit("No local X account is configured.")
    for account in accounts:
        print(
            f"@{account['username']} active={account['active']} "
            f"last_used={account['last_used'] or 'never'} error={account['error_msg'] or 'none'}"
        )


if __name__ == "__main__":
    main()
