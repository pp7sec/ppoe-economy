#!/usr/bin/env python3
"""Fetch PoEDB Economy summary (PoE1), reformat for Discord, and post.

- Reads the currently *Running* league from the homepage.
- Lifts "Divine Orb" (its price in chaos) to the top, then lists the next N items.
- Deletes this bot's previous messages in the target channel, then posts the new one.

Set env: DISCORD_BOT_TOKEN, and TARGET_CHANNEL (default below).
"""

import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

HOME_URL = "https://poedb.tw/us/"
URL = "https://poedb.tw/us/Economy"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

TARGET_CHANNELS = [c.strip() for c in os.environ.get("TARGET_CHANNEL", "111111111111111111").split(",") if c.strip()]
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API = "https://discord.com/api/v10"
SHOW = 20  # number of items after Divine Orb
SELF_ID = os.environ.get("DISCORD_SELF_ID", "")
# Invisible marker so each script only deletes its OWN previous posts
# (two scripts/bots may share a channel — never delete the other's).
MARKER = "\u200b\u200b"

# --- emoji config (ย้ายเซิร์ฟแค่แก้ emoji_config.json ตัวเดียว) ---
def _load_emoji():
    defaults = {"chaos": "<:chaos1:100000000000000001>", "divine": "<:divine1:100000000000000002>", "exalted": "<:exalted1:100000000000000003>"}
    for p in [pathlib.Path(__file__).with_name("emoji_config.json"), pathlib.Path("/root/.hermes/scripts/emoji_config.json")]:
        try:
            data = json.loads(p.read_text())
            cfg = data.get("poe1", data)
            # merge defaults with file values
            return {k: cfg.get(k, v) for k, v in defaults.items()}
        except Exception:
            continue
    return defaults

EMOJI = _load_emoji()


def current_league():
    """Return "Name (version)" of the league whose status is 'Running', else None."""
    html = requests.get(HOME_URL, headers=HEADERS, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("div.card"):
        hdr = card.select_one(".card-header")
        if not hdr:
            continue
        if not any(d.get_text(strip=True) == "Running for" for d in card.select("div")):
            continue
        ver_tag = hdr.find("small")
        version = ver_tag.get_text(strip=True) if ver_tag else ""
        name = hdr.get_text(" ", strip=True)
        if version:
            name = name.replace(version, "").strip()
            return f"{name} ({version})"
        return name
    return None


def scrape():
    html = requests.get(URL, headers=HEADERS, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    table = None
    for t in soup.select("table"):
        heads = [th.get_text(strip=True) for th in t.select("thead th")]
        if heads[:1] == ["Name"] and "24h volume traded" in heads:
            table = t
            break

    data = {}
    for tr in table.select("tbody tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 4:
            continue
        name_a = tds[0].find("a", href=re.compile(r"^Economy_"))
        name = name_a.get_text(strip=True) if name_a else tds[0].get_text(strip=True)

        vm = re.match(r"\s*([\d,.]+)", tds[1].get_text(" ", strip=True))
        value = vm.group(1).replace(",", "") if vm else ""
        priced = tds[1].find("a", href=re.compile(r"^Economy_"))
        priced_in = priced["href"].replace("Economy_", "") if priced else ""

        data[name] = {"value": value, "priced_in": priced_in}
    return data


def build_text(econ, league):
    sym = EMOJI
    lines = [league, "=" * len(league)]

    # lift Divine Orb to the top (price read in chaos as shown by the source)
    items = [(n, d["value"], sym.get(d["priced_in"].lower(), d["priced_in"]))
             for n, d in econ.items()]
    try:
        idx = next(i for i, (n, *_ ) in enumerate(items) if n == "Divine Orb")
    except StopIteration:
        idx = None

    if idx is not None:
        top = items.pop(idx)
        lines.append(f"• {top[0]} = {top[1]} {top[2]}")
        lines.append("")

    for n, v, u in items[:SHOW]:
        lines.append(f"• {n} = {v} {u}")
    return "\n".join(lines) + MARKER


def delete_old_messages():
    """Delete prior bot messages in the target channels."""
    if not TOKEN:
        print("no DISCORD_BOT_TOKEN; skipping delete", file=sys.stderr)
        return
    headers = {"Authorization": f"Bot {TOKEN}"}
    for channel in TARGET_CHANNELS:
        try:
            r = requests.get(f"{API}/channels/{channel}/messages?limit=50",
                             headers=headers, timeout=20)
            r.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            print(f"list messages failed ({channel}): {exc}", file=sys.stderr)
            continue
        for m in r.json():
            author = m.get("author", {})
            content = m.get("content", "") or ""
            if MARKER not in content:
                continue  # only touch our own previous posts
            if author.get("bot") and (not SELF_ID or author.get("id") == SELF_ID):
                try:
                    requests.delete(
                        f"{API}/channels/{channel}/messages/{m['id']}",
                        headers=headers, timeout=20,
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"delete {m['id']} failed: {exc}", file=sys.stderr)


def post(text):
    if not TOKEN:
        print("no DISCORD_BOT_TOKEN; not posting", file=sys.stderr)
        print(text)
        return
    headers = {"Authorization": f"Bot {TOKEN}",
               "Content-Type": "application/json"}
    for channel in TARGET_CHANNELS:
        r = requests.post(f"{API}/channels/{channel}/messages",
                          json={"content": text}, headers=headers, timeout=20)
        r.raise_for_status()


if __name__ == "__main__":
    league = current_league() or "Economy"
    econ = scrape()
    delete_old_messages()
    post(build_text(econ, league))