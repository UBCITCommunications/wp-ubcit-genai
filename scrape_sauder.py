import json, re
from datetime import datetime
from email.utils import format_datetime
from playwright.sync_api import sync_playwright

BASE    = "https://www.sauder.ubc.ca"
TARGET  = f"{BASE}/about-ubc-sauder/school-news/artificial-intelligence"
OUT_RSS = "sauder-ai.xml"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ))
        page.goto(TARGET, wait_until="networkidle", timeout=30000)

        articles = page.evaluate("""() => {
            const cards = [];
            const links = Array.from(document.querySelectorAll('a[href*="/news/school-news/"]'))
                .filter(a => a.textContent.includes('Card link for'));

            links.forEach(link => {
                let el    = link.nextElementSibling;
                let title = '', date = '', category = '', image = '';

                // heading
                while (el && !/^H\\d$/.test(el.tagName)) el = el.nextElementSibling;
                if (el) { title = el.textContent.trim(); el = el.nextElementSibling; }

                // ul → category + date
                while (el && el.tagName !== 'UL') el = el.nextElementSibling;
                if (el) {
                    el.querySelectorAll('li').forEach(li => {
                        const t = li.textContent.trim();
                        if (/January|February|March|April|May|June|July|August|September|October|November|December/.test(t))
                            date = t;
                        else
                            category = t;
                    });
                    el = el.nextElementSibling;
                }

                // image
                while (el) {
                    const img = el.tagName === 'IMG' ? el : el.querySelector('img');
                    if (img && img.src) { image = img.src; break; }
                    el = el.nextElementSibling;
                }

                if (title) cards.push({ url: link.href, title, date, category, image });
            });
            return cards;
        }""")

        browser.close()
        return articles

def parse_date(s):
    try:
        return format_datetime(datetime.strptime(s.strip(), "%B %d, %Y"))
    except Exception:
        return format_datetime(datetime.now())

def build_rss(articles):
    items = []
    for a in articles:
        img_tags = ""
        if a.get("image"):
            img_tags = (
                f'<enclosure url="{a["image"]}" type="image/jpeg" length="0"/>\n'
                f'        <media:content url="{a["image"]}" medium="image"/>\n'
                f'        <media:thumbnail url="{a["image"]}"/>'
            )
        items.append(f"""
    <item>
      <title><![CDATA[{a["title"]}]]></title>
      <link>{a["url"]}</link>
      <guid isPermaLink="true">{a["url"]}</guid>
      <pubDate>{parse_date(a["date"])}</pubDate>
      <category><![CDATA[{a.get("category", "")}]]></category>
      {img_tags}
    </item>""")

    now = format_datetime(datetime.now())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:media="http://search.yahoo.com/mrss/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>UBC Sauder - Artificial Intelligence News</title>
    <link>{TARGET}</link>
    <description>AI news from UBC Sauder School of Business</description>
    <lastBuildDate>{now}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>"""

if __name__ == "__main__":
    articles = scrape()
    print(f"Found {len(articles)} articles")
    rss = build_rss(articles)
    with open(OUT_RSS, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Written to {OUT_RSS}")
