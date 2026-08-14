import sys, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import format_datetime

BASE     = "https://www.cs.ubc.ca"
TAG_PAGE = f"{BASE}/category/tags/ai"
OUT_RSS  = "cs-ubc-ai.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0",
    "Accept": "text/html,application/xhtml+xml",
}

def scrape():
    r = requests.get(TAG_PAGE, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    articles = []
    for article in soup.select("article.node--type-news"):
        link_el = article.select_one("h4.news--teaser__header a")
        if not link_el:
            continue
        url   = BASE + link_el["href"]
        title = link_el.get_text(strip=True)

        time_el  = article.select_one("time[datetime]")
        date_iso = time_el["datetime"] if time_el else ""

        summary_el = article.select_one(".news--teaser__summary")
        summary    = summary_el.get_text(" ", strip=True) if summary_el else ""

        img   = article.select_one("img.image-style-story-thumb")
        image = BASE + img["src"].split("?")[0] if img else ""

        articles.append({"title": title, "url": url,
                         "date": date_iso, "summary": summary, "image": image})
        print(f"  [{date_iso[:10]}] {title[:70]}")

    return articles

def parse_date(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
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
      <description><![CDATA[{a["summary"]}]]></description>
      <pubDate>{parse_date(a["date"])}</pubDate>{img_tags}
    </item>""")

    now = format_datetime(datetime.now(tz=timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>UBC Computer Science - AI News</title>
    <link>{TAG_PAGE}</link>
    <description>AI-tagged news from UBC Department of Computer Science</description>
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
