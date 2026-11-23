#!/usr/bin/env python3
"""The posting feeds: one RSS feed per channel, holding the posts of schedule.json whose time has come.

    python3 scripts/feeds.py [--now 2026-11-24T10:05]      writes feeds/*.xml

Zapier's free plan allows two-step Zaps, and "RSS by Zapier, New Item in Feed" costs no task: so each channel is one
Zap, "new item in its feed -> post it". A post enters the feeds at its slot (publish_date + slot, Europe/Stockholm);
the GitHub Action runs at the slots and commits the feeds. Feeds (newest first, the last 30 items):
  youtube.xml          videos: title = Shorts title, description = Shorts description, enclosure = the video
  instagram-reels.xml  videos: description = Instagram caption, enclosure = the video
  instagram-photos.xml cards:  description = Instagram caption, enclosure = the picture
  tiktok.xml           videos: description = TikTok caption, enclosure = the video
  reddit.xml           the day's first post only (one Reddit post a day), for a text post: title = Reddit title,
                       description = the body, the media link and the "I work on the game." links (a two-step Zap
                       cannot add a first comment, so the links go into the post)
"""
import argparse
import datetime as dt
import json
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("Europe/Stockholm")


def when(p):
    d = dt.date.fromisoformat(p["publish_date"])
    return dt.datetime(d.year, d.month, d.day, int(p["slot"]), 0, tzinfo=TZ)


def feed(name, title, items):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>',
           f"<title>{escape(title)}</title><link>https://github.com/SpaceCorps/promo-media</link>",
           f"<description>{escape(title)}</description>"]
    for it in items:
        mime = "video/mp4" if it["url"].endswith(".mp4") else "image/jpeg"
        out.append("<item>"
                   f"<title>{escape(it['title'])}</title>"
                   f"<description>{escape(it['description'])}</description>"
                   f"<link>{escape(it['url'])}</link>"
                   f'<guid isPermaLink="false">{escape(name + "-" + it["version"])}</guid>'
                   f"<pubDate>{format_datetime(it['when'])}</pubDate>"
                   f'<enclosure url="{escape(it["url"])}" type="{mime}" length="0"/>'
                   "</item>")
    out.append("</channel></rss>")
    (ROOT / "feeds").mkdir(exist_ok=True)
    (ROOT / "feeds" / f"{name}.xml").write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--now")
    a = ap.parse_args()
    now = dt.datetime.fromisoformat(a.now).replace(tzinfo=TZ) if a.now else dt.datetime.now(TZ)
    posts = [p for p in json.loads((ROOT / "schedule.json").read_text()) if p.get("status", "queued") != "skip"]
    due = sorted((p for p in posts if when(p) <= now), key=when, reverse=True)[:30]

    def items(sel, title, desc):
        out = [{"version": p["version"], "url": p["media_url"], "when": when(p), "title": title(p), "description": desc(p)}
               for p in due if sel(p)]
        # one sample at the bottom, dated before the series: Zapier needs an item to set a Zap up, and a Zap never
        # posts the items that were already in its feed when it was switched on
        first = next((p for p in sorted(posts, key=when) if sel(p)), None)
        if first:
            out.append({"version": "sample", "url": first["media_url"], "when": dt.datetime(2026, 11, 1, 12, tzinfo=TZ),
                        "title": title(first), "description": desc(first)})
        return out

    vid = lambda p: p["kind"] == "video"
    feed("youtube", "SpaceCorps promo: YouTube Shorts", items(vid, lambda p: p["shorts_title"], lambda p: p["shorts_description"]))
    feed("instagram-reels", "SpaceCorps promo: Instagram Reels", items(vid, lambda p: p["version"], lambda p: p["instagram_caption"]))
    feed("instagram-photos", "SpaceCorps promo: Instagram photos",
         items(lambda p: p["kind"] == "card", lambda p: p["version"], lambda p: p["instagram_caption"]))
    feed("tiktok", "SpaceCorps promo: TikTok", items(vid, lambda p: p["version"], lambda p: p["tiktok_caption"]))
    media = lambda p: ("Video: " if p["kind"] == "video" else "Picture: ") + p["media_url"]
    feed("reddit", "SpaceCorps promo: Reddit", items(lambda p: p["reddit"] == "yes", lambda p: p["reddit_title"],
                                                     lambda p: p["reddit_body"] + "\n\n" + media(p) + "\n\n" + p["reddit_first_comment"]))
    print(f"feeds: {len(due)} posts due at {now:%Y-%m-%d %H:%M}, next: "
          + next((f"{p['version']} at {when(p):%Y-%m-%d %H:%M}" for p in sorted(posts, key=when) if when(p) > now), "none"))


if __name__ == "__main__":
    main()
