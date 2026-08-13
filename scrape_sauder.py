import sys, requests
from datetime import datetime
from email.utils import format_datetime

BASE    = "https://www.sauder.ubc.ca"
API     = (f"{BASE}/api/article_list?_format=json&limit=20&order="
           "&type=article_list&article_type[]=667&article_topic[]=1144")
OUT_RSS = "sauder-ai.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0",
    "Referer": f"{BASE}/about-ubc-sauder/school-news/artificial-intelligence",
}

def scrape():
    r = requests.get(API, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    items = data.get("results", {})
    print(f"API returned {len(items)} items")

    articles = []
    for nid, item in items.items():
        ref   = item.get("reference", {})
        node  = item.get("node", {})

        titles = ref.get("field_reference_title") or node.get("title", [])
        title  = titles[0]["value"].strip() if titles else ""

        url    = BASE + item.get("url", "")

        descs  = ref.get("field_reference_description", [])
        desc   = descs[0]["value"].strip() if descs else ""

        imgs   = ref.get("field_reference_image", [])
        image  = BASE + imgs[0]["url"] if imgs else ""

        dates  = node.get("field_display_date", [])
        date   = dates[0]["value"] if dates else ""  # "2026-07-24"

        if title and url:
            articles.append({"title": title, "url": url,
                             "desc": desc, "image": image, "date": date})
            print(f"  [{date}] {title[:70]}")

    return articles


def parse_date(s):
    try:
        return format_datetime(datetime.strptime(s, "%Y-%m-%d"))
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
