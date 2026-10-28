
import os
import json
import hashlib
import requests
import feedparser

from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

RSS_URL = (
    "https://news.google.com/rss/search"
    "?q=sepak+bola&hl=id&gl=ID&ceid=ID:id"
)

PAGE_ID = os.environ["FB_PAGE_ID"]
PAGE_TOKEN = os.environ["FB_PAGE_TOKEN"]
GRAPH_VERSION = os.environ["FB_GRAPH_VERSION"]

# Gambar cadangan sepak bola dari Unsplash.
FALLBACK_IMAGE_URL = (
    "https://images.unsplash.com/"
    "photo-1574629810360-7efbbe195018"
    "?auto=format&fit=crop&w=1200&q=85"
)

STATE_FILE = Path("posted.json")
MAX_POSTS_PER_RUN = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BolaLagiPanasBot/1.0)"
}


def load_posted():
    if STATE_FILE.exists():
        try:
            return json.loads(
                STATE_FILE.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            print("Riwayat tidak terbaca; mulai dengan daftar kosong.")
    return []


def get_article_image(item):
    """Cari gambar dari RSS, lalu metadata artikel."""
    # Coba gambar yang disediakan RSS.
    for field in ("media_content", "media_thumbnail", "enclosures"):
        for media in item.get(field, []):
            image_url = media.get("url", "")
            media_type = media.get("type", "")

            if image_url and (
                media_type.startswith("image/")
                or field != "enclosures"
                or not media_type
            ):
                return image_url

    # Coba metadata gambar pada halaman artikel.
    article_url = item.get("link", "").strip()
    if not article_url:
        return None

    try:
        response = requests.get(
            article_url,
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for attrs in (
            {"property": "og:image"},
            {"name": "twitter:image"},
            {"property": "og:image:url"},
        ):
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                return urljoin(
                    response.url,
                    tag["content"].strip(),
                )

    except requests.RequestException as exc:
        print("Tidak bisa membaca gambar artikel:", exc)

    return None


def publish_photo(image_url, caption):
    """Publikasikan foto dan caption ke Facebook Page."""
    endpoint = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/{PAGE_ID}/photos"
    )

    response = requests.post(
        endpoint,
        data={
            "url": image_url,
            "caption": caption,
            "access_token": PAGE_TOKEN,
        },
        timeout=60,
    )

    try:
        result = response.json()
    except ValueError:
        result = {}

    if response.ok and result.get("id"):
        return result

    print("Foto gagal dipublikasikan:", result or response.text)
    return None


def main():
    posted = load_posted()
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("RSS kosong atau tidak bisa dibaca.")
        return

    count = 0

    for item in feed.entries:
        url = item.get("link", "").strip()
        title = item.get("title", "").strip()

        if not url or not title:
            continue

        news_id = hashlib.sha256(url.encode()).hexdigest()

        if news_id in posted:
            continue

        # Ambil gambar artikel; jika tidak ada, gunakan gambar cadangan.
        image_url = get_article_image(item)
        using_fallback = not bool(image_url)

        if using_fallback:
            image_url = FALLBACK_IMAGE_URL

        caption = (
            f"⚽ BOLA LAGI PANAS!\n\n"
            f"{title}\n\n"
            f"Baca berita selengkapnya melalui sumber:\n"
            f"{url}\n\n"
            f"#BolaLagiPanas #BeritaSepakBola"
        )

        result = publish_photo(image_url, caption)

        # Jika gambar asli gagal, coba sekali lagi dengan gambar cadangan.
        if not result and not using_fallback:
            print("Mencoba gambar cadangan sepak bola...")
            result = publish_photo(FALLBACK_IMAGE_URL, caption)

        if result:
            posted.append(news_id)
            count += 1
            print(
                "Berhasil posting:",
                title,
                "| Gambar cadangan:" if using_fallback else "| Gambar artikel:",
                "Ya" if using_fallback else "Tidak",
            )
        else:
            print("Posting gagal:", title)
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
