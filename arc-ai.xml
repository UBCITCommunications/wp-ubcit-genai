import sys, requests, re
from datetime import datetime
from email.utils import format_datetime

BASE    = "https://arc.ubc.ca"
API     = (f"{BASE}/jsonapi/node/ubc_announcement"
           "?filter[field_announcement_tags.name]=Artificial_Intelligence"
           "&include=field_announcement_feature_image"
           "&sort=-created"
           "&page[limit]=20")
OUT_RSS = "arc-ai.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0",
    "Accept": "application/vnd.api+json",
}


def strip_html(html):
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def scrape():
    r = requests.get(API, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()

    images = {}
    for f in data.get("included", []):
        if f.get("type") == "file--file":
            url = f.get("attributes", {}).get("uri", {}).get("url", "")
            if url:
                images[f["id"]] = BASE + url

    articles = []
    for node in data.get("data", []):
        attrs = node.get("attributes", {})
        rels  = node.get("relationships", {})

        title = attrs.get("title", "").strip()
        nid   = attrs.get("drupal_internal__nid")
        alias = (attrs.get("path") or {}).get("alias")
        url   = BASE + alias if alias else f"{BASE}/node/{nid}"
        date  = attrs.get("created", "")

        body  = attrs.get("body") or {}
        desc  = strip_html(body.get("summary") or body.get("processed", ""))[:300]

        img_rel = rels.get("field_announcement_feature_image", {}).get("data") or {}
        image   = images.get(img_rel.get("id"), "")

        if title and url:
            articles.append({"title": title, "url": url,
                             "date": date, "desc": desc, "image": image})
            print(f"  [{date[:10]}] {title[:70]}")

    print(f"Found {len(articles)} articles")
    return articles


def parse_date(s):
    try:
        return format_datetime(datetime.fromisoformat(s.replace("Z", "+00:00")))
    except Exception:
        return format_datetime(datetime.now())


def build_rss(articles):
    items = []
    for a in articles:
        img_tags = ""
        if a["image"]:
            img_tags = (
                f'\n      <enclosure url="{a["image"]}" type="image/jpeg" length="0"/>'
                f'\n      <media:content url="{a["image"]}" medium="image"/>'
            )
        items.append(f"""
    <item>
      <title><![CDATA[{a["title"]}]]></title>
      <link>{a["url"]}</link>
      <guid isPermaLink="true">{a["url"]}</guid>
      <description><![CDATA[{a["desc"]}]]></description>
      <pubDate>{parse_date(a["date"])}</pubDate>{img_tags}
    </item>""")

    now = format_datetime(datetime.now())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>UBC ARC - AI News</title>
    <link>{BASE}/news-events</link>
    <description>AI news from UBC Advanced Research Computing</description>
    <lastBuildDate>{now}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>"""


if __name__ == "__main__":
    try:
        articles = scrape()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not articles:
        print("No articles found — RSS not written.")
        sys.exit(1)

    rss = build_rss(articles)
    with open(OUT_RSS, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Written {len(articles)} items to {OUT_RSS}")
