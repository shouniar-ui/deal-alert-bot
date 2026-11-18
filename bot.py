"""Deal alert bot.

Checks deal feeds, keeps the deals that match config.yaml, and posts new ones
to Telegram and/or Discord. Also posts your own affiliate deals from my_deals.csv.
You should not need to edit this file: change config.yaml and my_deals.csv instead.
"""

import csv
import html
import json
import os
import re
import sys
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import feedparser
import requests
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(HERE, "seen.json")
MY_DEALS_FILE = os.path.join(HERE, "my_deals.csv")
USER_AGENT = "Mozilla/5.0 (compatible; DealAlertBot/1.0)"
PRICE_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
AMAZON_TAG = os.environ.get("AMAZON_TAG", "").strip()
DRY_RUN = os.environ.get("DRY_RUN") == "1"


def load_config():
    with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_seen():
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen[-3000:], f, indent=0)


def find_price(text):
    m = PRICE_RE.search(text or "")
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def has_word(text, word):
    """True if word appears as a whole word/phrase (so 'tv' doesn't match 'atv')."""
    return re.search(r"(?<![a-z0-9])" + re.escape(str(word).lower()) + r"(?![a-z0-9])", text) is not None


def matches(title, cfg):
    t = title.lower()
    include = cfg.get("include_keywords") or []
    exclude = cfg.get("exclude_keywords") or []
    if include and not any(has_word(t, k) for k in include):
        return False
    if any(has_word(t, k) for k in exclude):
        return False
    max_price = cfg.get("max_price")
    if max_price:
        price = find_price(title)
        if price is not None and price > float(max_price):
            return False
    return True


def add_affiliate_tag(url):
    """Adds your Amazon Associates tag to any direct Amazon link."""
    if not AMAZON_TAG or not url:
        return url
    parts = urlparse(url)
    host = parts.netloc.lower()
    if not (host.endswith("amazon.com") or host == "amzn.to"):
        return url
    query = dict(parse_qsl(parts.query))
    query["tag"] = AMAZON_TAG
    return urlunparse(parts._replace(query=urlencode(query)))


def fetch_feed(url):
    if os.path.exists(url):  # local file, used for testing
        return feedparser.parse(url)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def format_message(title, url, cfg, label=None):
    price = find_price(title)
    lines = [f"{cfg.get('emoji', '🔥')} <b>{html.escape(title)}</b>"]
    if price is not None:
        lines.append(f"💲 ${price:,.2f}")
    lines.append(f'🛒 <a href="{html.escape(url, quote=True)}">Get the deal</a>')
    if label:
        lines.append(label)
    footer = cfg.get("footer")
    if footer:
        lines.append(f"<i>{html.escape(footer)}</i>")
    return "\n".join(lines)


def html_to_discord(text):
    text = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r"[\2](\1)", text)
    text = text.replace("<b>", "**").replace("</b>", "**")
    text = text.replace("<i>", "*").replace("</i>", "*")
    return html.unescape(text)


def send(text):
    if DRY_RUN:
        print("---- would post ----\n" + text)
        return True
    ok = True
    if TELEGRAM_TOKEN and TELEGRAM_CHAT:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"},
            timeout=20,
        )
        if not r.ok:
            print(f"Telegram error: {r.status_code} {r.text}", file=sys.stderr)
            ok = False
    if DISCORD_WEBHOOK:
        r = requests.post(
            DISCORD_WEBHOOK,
            json={"content": html_to_discord(text)[:2000]},
            timeout=20,
        )
        if not r.ok:
            print(f"Discord error: {r.status_code} {r.text}", file=sys.stderr)
            ok = False
    time.sleep(1.5)  # stay well under Telegram/Discord rate limits
    return ok


def collect_feed_deals(cfg, seen_set):
    deals = []
    for feed in cfg.get("feeds") or []:
        url = feed["url"] if isinstance(feed, dict) else feed
        try:
            parsed = fetch_feed(url)
        except Exception as e:  # one broken feed shouldn't stop the others
            print(f"Could not read feed {url}: {e}", file=sys.stderr)
            continue
        for entry in parsed.entries:
            deal_id = entry.get("id") or entry.get("link")
            title = (entry.get("title") or "").strip()
            link = entry.get("link") or ""
            if not deal_id or not title or deal_id in seen_set:
                continue
            deals.append({"id": deal_id, "title": title, "url": link})
    return deals


def collect_my_deals(seen_set):
    """Your own deals (with your affiliate links) from my_deals.csv."""
    if not os.path.exists(MY_DEALS_FILE):
        return []
    deals = []
    with open(MY_DEALS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            title = (row.get("title") or "").strip()
            url = (row.get("url") or "").strip()
            if not title or not url:
                continue
            deal_id = "mine:" + url
            if deal_id not in seen_set:
                deals.append({"id": deal_id, "title": title, "url": url})
    return deals


def main():
    cfg = load_config()
    if not DRY_RUN and not ((TELEGRAM_TOKEN and TELEGRAM_CHAT) or DISCORD_WEBHOOK):
        sys.exit("No Telegram or Discord settings found. See README step 3.")

    seen = load_seen()
    seen_set = set(seen)
    first_run = not seen
    max_posts = int(cfg.get("max_posts_per_run", 5))

    mine = collect_my_deals(seen_set)
    feed_deals = collect_feed_deals(cfg, seen_set)
    matching = [d for d in feed_deals if matches(d["title"], cfg)]

    posted = 0
    for deal in mine:  # your own deals always go out
        if send(format_message(deal["title"], add_affiliate_tag(deal["url"]), cfg, "⭐ Featured")):
            seen.append(deal["id"])
            posted += 1

    for deal in matching[:max_posts]:
        if send(format_message(deal["title"], add_affiliate_tag(deal["url"]), cfg)):
            seen.append(deal["id"])
            posted += 1

    # Mark everything else as seen so the channel isn't flooded with old deals
    # (on the first run, or when more deals arrive than max_posts_per_run).
    for deal in feed_deals:
        if deal["id"] not in seen:
            seen.append(deal["id"])

    save_seen(seen)
    note = " (first run: older deals skipped)" if first_run else ""
    print(f"Checked {len(feed_deals)} new items, {len(matching)} matched, posted {posted}{note}.")


if __name__ == "__main__":
    main()
