import re, sys
from datetime import datetime
from email.utils import format_datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE    = "https://www.sauder.ubc.ca"
TARGET  = f"{BASE}/about-ubc-sauder/school-news/artificial-intelligence"
OUT_RSS = "sauder-ai.xml"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(TARGET, wait_until="domcontentloaded", timeout=60000)

        try:
            page.wait_for_selector('main a[href*="/news/school-news/"]', timeout=20000)
        except PWTimeout:
            print("ERROR: No news links found after 20s. Page source:")
            print(page.content()[:3000])
            browser.close()
            return []

        page.wait_for_timeout(2000)
        print(f"Page title: {page.title()}")

        articles = page.evaluate("""() => {
            const articles = [];
            const seen    = new Set();
            const main    = document.querySelector('main') || document.body;

            // Work backwards from headings — each article heading is preceded by its card link
            const headings = Array.from(main.querySelectorAll('h2, h3, h4'));

            headings.forEach(h => {
                const prev = h.previousElementSibling;

                if (!prev || prev.tagName !== 'A') return;
                if (!prev.href.includes('/news/school-news/')) return;
                if (seen.has(prev.href)) return;
                seen.add(prev.href);

                const title = h.textContent.trim();
                let date = '', category = '', image = '';

                let el = h.nextElementSibling;
                for (let i = 0; i < 6 && el; i++, el = el.nextElementSibling) {
                    if (el.tagName === 'UL') {
                        el.querySelectorAll('li').forEach(li => {
                            const t = li.textContent.trim();
                            if (/January|February|March|April|May|June|July|August|September|October|November|December/.test(t))
                                date = t;
                            else if (t)
                                category = t;
                        });
                    }
                    const img = el.tagName === 'IMG' ? el : el.querySelector('img');
                    if (img && img.src) image = img.src;
                }

                articles.push({ url: prev.href, title, date, category, image });
            });

            return articles;
        }""")

        browser.close()
        print(f"Found {len(articles)} articles")
        for a in articles:
            print(f"  [{a['date']}] {a['title'][:70]}")
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
    <link>{TARGET}</link>
    <description>AI news from UBC Sauder School of Business</description>
    <lastBuildDate>{now}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>"""


if __name__ == "__main__":
    articles = scrape()
    if not articles:
        print("No articles found — RSS not written.")
        sys.exit(1)
    rss = build_rss(articles)
    with open(OUT_RSS, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Written {len(articles)} items to {OUT_RSS}")
