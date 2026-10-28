
def get_article_image(item):
    """Cari gambar asli dari halaman artikel, hindari logo Google News."""
    article_url = item.get("link", "").strip()

    if not article_url:
        return None

    try:
        response = requests.get(
            article_url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Prioritaskan metadata gambar milik halaman artikel.
        for attrs in (
            {"property": "og:image"},
            {"property": "og:image:url"},
            {"name": "twitter:image"},
            {"name": "twitter:image:src"},
        ):
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                image_url = urljoin(
                    response.url,
                    tag["content"].strip(),
                )

                # Jangan gunakan gambar yang berasal dari logo Google News.
                host = image_url.lower()
                if "news.google.com" not in host:
                    return image_url

    except (requests.RequestException, ValueError) as exc:
        print("Gagal mengambil gambar artikel:", exc)

    return None
