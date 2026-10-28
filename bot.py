
import os
import json
import hashlib
from pathlib import Path

import requests
import feedparser

RSS_URL = (
    "https://news.google.com/rss/search"
    "?q=sepak+bola&hl=id&gl=ID&ceid=ID:id"
)

PAGE_ID = os.environ["FB_PAGE_ID"]
PAGE_TOKEN = os.environ["FB_PAGE_TOKEN"]
GRAPH_VERSION = os.environ["FB_GRAPH_VERSION"]

STATE_FILE = Path("posted.json")
MAX_POSTS_PER_RUN = 3


def load_posted():
    if STATE_FILE.exists():
        return json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    return []


def main():
    posted = load_posted()
    feed = feedparser.parse(RSS_URL)
    count = 0

    for item in feed.entries:
        url = item.get("link", "").strip()
        title = item.get("title", "").strip()

        if not url or not title:
            continue

        news_id = hashlib.sha256(
            url.encode()
        ).hexdigest()

        if news_id in posted:
            continue

        message = (
            f"⚽ BOLA LAGI PANAS!\n\n"
            f"{title}\n\n"
            f"Baca berita selengkapnya:\n{url}\n\n"
            f"#BolaLagiPanas #SepakBola"
        )

        endpoint = (
            f"https://graph.facebook.com/"
            f"{GRAPH_VERSION}/{PAGE_ID}/feed"
        )

        response = requests.post(
            endpoint,
            data={
                "message": message,
                "access_token": PAGE_TOKEN,
            },
            timeout=30,
        )

        result = response.json()

        if response.ok and result.get("id"):
            posted.append(news_id)
            count += 1
            print("Berhasil:", title)
        else:
            print("Gagal:", result)
            break

        if count >= MAX_POSTS_PER_RUN:
            break

    STATE_FILE.write_text(
        json.dumps(
            posted[-2000:],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Jumlah posting:", count)


if __name__ == "__main__":
    main()
