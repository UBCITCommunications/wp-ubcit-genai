import sys, requests
from datetime import datetime
from email.utils import format_datetime

BASE    = "https://www.sauder.ubc.ca"
API     = (f"{BASE}/api/article_list?_format=json"
           "&limit=20&order=&type=article_list"
           "&article_type[]=667&article_topic[]=1144")
OUT_RSS = "sauder-ai.xml"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"),
    "Accept": "application/json",
}

def scrape():
    r = requests.get(API, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"API returned {len(data)} items")

    articles = []
    for item in data:
        title = (item.get("title") or "").strip()
        path  = item.get("url") or item.get("path") or ""
        url   = path if path.startswith("http") else BASE + path

        # date — try common field names
        date_raw = (item.get("date") or item.get("created")
                    or item.get("field_date") or "")

        # image — try common field names, make absolute
        image = (item.get("image") or item.get("field_image")
                 or item.get("thumbnail") or "")
        if image and not image.startswith("http"):
            image = BASE + image

        category = (item.get("category") or item.get("topic")
                    or item.get("field_category") or "")

        if title and url:
            articles.append({"title": title, "url": url,
                             "date": str(date_raw), "category": str(category),
                             "image": image})
            print(f"  [{date_raw}] {title[:70]}")

    return articles


def parse_date(s):
    # try "Month DD, YYYY" first, then ISO, then now
    for fmt in ("%B %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return format_datetime(datetime.strptime(s.strip(), fmt))
        except Exception:
            pass
    # Unix timestamp?
    try:
        return format_datetime(datetime.fromtimestamp(int(s)))
    except Exception:
        pass
    return format_datetime(datetime.now())


def build_rss(articles):
    items = []
    for a in articles:
        img_tags = ""
        if a.get("image"):
            img_tags = (
                f'\n      <enclosure url="{a["image"]}" type="image/jpeg" length="0"/>'
                f'\n      <media:content url="{a["image"]}" medium="image"/>'
                f'\n      <media:thumbnail url="{a["image"]}"/>'
            )
        items.append(f"""
    <item>
      <title><![CDATA[{a["title"]}]]></title>
      <link>{a["url"]}</link>
      <guid isPermaLink="true">{a["url"]}</guid>
      <pubDate>{parse_date(a["date"])}</pubDate>
      <category><![CDATA[{a.get("category", "")}]]></category>{img_tags}
    </item>""")

    now = format_datetime(datetime.now())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:media="http://search.yahoo.com/mrss/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>UBC Sauder - Artificial Intelligence News</title>
    <link>{BASE}/about-ubc-sauder/school-news/artificial-intelligence</link>
    <description>AI news from UBC Sauder School of Business</description>
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
