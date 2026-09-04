#!/usr/bin/env python3
"""Fetch PoE2DB Economy summary (PoE2), reformat for Discord, and post.

- Reads the currently *Running* league from the poe2db homepage.
- Parses prices correctly (item rate = left / right, fiscally one per ref):
  value cell is "<left_num> <ref> <-> <right_num> <item>".
- Lifts the two main currencies (Divine Orb in chaos, Exalted Orb in divine) to the top.
- Deletes this bot's previous messages in the target channel, then posts the new one.

Set env: DISCORD_BOT_TOKEN. TARGET_CHANNEL defaults to the PoE2 economy channel.
"""

import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

HOME_URL = "https://poe2db.tw/us/"
URL = "https://poe2db.tw/us/Economy"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

TARGET_CHANNELS = [c.strip() for c in os.environ.get("TARGET_CHANNEL", "222222222222222222").split(",") if c.strip()]
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API = "https://discord.com/api/v10"
SHOW = 20  # number of items after the two pinned currencies
SELF_ID = os.environ.get("DISCORD_SELF_ID", "")

# (name, priced_in-without-slash) to lift to the top, in order
PINNED = [("Divine Orb", "chaos"), ("Exalted Orb", "divine")]

def _load_emoji():
    defaults = {"chaos": "<:chaos2:200000000000000001>", "divine": "<:divine2:200000000000000002>", "exalted": "<:exalted2:200000000000000003>"}
    for p in [pathlib.Path(__file__).with_name("emoji_config.json"), pathlib.Path("/root/.hermes/scripts/emoji_config.json")]:
        try:
            data = json.loads(p.read_text())
            cfg = data.get("poe2", data)
            return {k: cfg.get(k, v) for k, v in defaults.items()}
        except Exception:
            continue
    return defaults

SYM = _load_emoji()
CHAOS_EMOJI = SYM["chaos"]
DIVINE_EMOJI = SYM["divine"]

# Invisible marker so each script only deletes its OWN previous posts
# (two scripts/bots may share a channel — never delete the other's).
MARKER = "\u200b\u200b\u200b"


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


def _fmt(x: float) -> str:
    """Trim a price to a readable form (e.g. 6094, 12.7, 0.382)."""
    if x >= 100:
        return str(int(round(x)))
    return f"{x:.3g}"


def parse_value(cell):
    """Return (rate_str, unit) from a value cell, the way the site shows it.

    Cell is '<left_num> <ref> <-> <right_num> <item>'.
      - Expensive item (item side is 1): price per item, e.g. ("6094", "divine").
      - Cheap item (ref side is 1): count per 1 ref, e.g. ("401", "/divine").
    """
    nums = re.findall(r"[\d,.]+", cell.get_text(" ", strip=True))
    anchors = cell.find_all("a", href=re.compile(r"^Economy_"))
    if len(nums) < 2 or len(anchors) < 1:
        return "", ""
    left = float(nums[0].replace(",", ""))
    right = float(nums[1].replace(",", ""))
    ref = anchors[0]["href"].replace("Economy_", "")
    if left >= right:  # item is worth >= 1 ref -> price per item
        return _fmt(left / right if right else left), ref
    # item cheaper than ref -> how many you get per 1 ref
    return _fmt(right / left if left else right), "/" + ref


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

        # item always on right: price of 1 item = left_num / right_num in ref currency
        value, priced_in = parse_value(tds[1])

        data[name] = {"value": value, "priced_in": priced_in}
    return data


def mark_for(unit):
    """Short symbol for display; handle '/unit' (per-ref) as '/X'."""
    slash = unit.startswith("/")
    key = unit.lstrip("/").lower()
    sym = SYM.get(key, key)
    return ("/" if slash else "") + sym


def build_text(econ, league):
    lines = [league, "=" * len(league)]

    # สองบรรทัดแรก: แสดงมูลค่า Divine Orb ในหน่วย chaos และ exalted
    # (จากข้อมูล: 1 Divine = 11.8 chaos, 1 Divine = 412 exalted)
    div_hit = econ.get("Divine Orb")
    ex_hit = econ.get("Exalted Orb")
    if div_hit:
        lines.append(f"• Divine Orb = {div_hit['value']} {mark_for(div_hit['priced_in'])}")
    if ex_hit:
        lines.append(f"• Divine Orb = {ex_hit['value']} {SYM['exalted']}")
    if div_hit or ex_hit:
        lines.append("")

    pinned_done = {name for name, _ in PINNED if econ.get(name)}
    excluded = pinned_done
    count = 0
    for name, d in econ.items():
        if name in excluded:
            continue
        m = mark_for(d["priced_in"])
        lines.append(f"• {name} = {d['value']} {m}")
        count += 1
        if count >= SHOW:
            break
    return "\n".join(lines) + MARKER


def delete_old_messages():
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