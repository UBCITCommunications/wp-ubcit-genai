import re, sys, requests
from datetime import datetime, timezone
from email.utils import format_datetime

BASE    = "https://aihealth.med.ubc.ca"
API     = f"{BASE}/wp-json/wp/v2/posts?per_page=100&_embed=1&orderby=date&order=desc"
OUT_RSS = "aihealth-ai.xml"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).strip()

def get_image(post):
    try:
        media = post["_embedded"]["wp:featuredmedia"]
        if media and media[0].get("source_url"):
            return media[0]["source_url"]
    except (KeyError, IndexError, TypeError):
        pass
    return ""

def scrape():
    r = requests.get(API, headers=HEADERS, timeout=30)
    r.raise_for_status()
    posts = r.json()
    print(f"API returned {len(posts)} posts")

    articles = []
    for post in posts:
        title   = strip_html(post["title"]["rendered"])
        url     = post["link"]
        date    = post["date"]
        excerpt = strip_html(post["excerpt"]["rendered"])
        image   = get_image(post)
        articles.append({"title": title, "url": url,
                         "date": date, "excerpt": excerpt, "image": image})
        print(f"  [{date[:10]}] {title[:70]}")

    return articles

def parse_date(iso):
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return format_datetime(dt)
    except Exception:
        return format_datetime(datetime.now(tz=timezone.utc))

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
      <description><![CDATA[{a["excerpt"]}]]></description>
      <pubDate>{parse_date(a["date"])}</pubDate>{img_tags}
    </item>""")

    now = format_datetime(datetime.now(tz=timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>UBC AI &amp; Health Network - News</title>
    <link>{BASE}/news-events/</link>
    <description>News from the UBC AI &amp; Health Network</description>
    <lastBuildDate>{now}</lastBuildDate>
    {"".join(items)}
  </channel>
</rss>"""

if __name__ == "__main__":
    try:
        articles = scrape()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    if not articles:
        print("No articles found.")
        sys.exit(1)
    rss = build_rss(articles)
    with open(OUT_RSS, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Written {len(articles)} items to {OUT_RSS}")
