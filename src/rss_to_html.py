import feedparser
import os
import shutil
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# import certifi
# ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

def parse_rss_feed(url: str):
    feed = feedparser.parse(url)
    feed_title = feed.feed.get('title', 'Unknown feed')
    if feed.bozo:
        print(f"Feed.bozo_exception: {feed.bozo_exception}  for URL: {url}")
    print(f"Fetching {len(feed.entries)} items from {feed_title}")
    items = []
    for entry in feed.entries:
        entry_title = entry.get("title", "No title")
        entry_title = entry_title.replace("<strong>", "").replace("</strong>", "")
        entry_title_rsplit = entry_title.rsplit(" - ", 1) # Google News formats titles like "Headline - Source"
        if len(entry_title_rsplit) == 2:
            entry_title_cleaned = f"{entry_title_rsplit[0]} [{entry_title_rsplit[1]}]"
        else:
            entry_title_cleaned = entry_title
        items.append({
            "title": entry_title_cleaned,
            "description": entry.get("description", ""),
            "link": entry.get("link", ""),
        })
    return items, feed.feed.get("updated", None)

def generate_news_html():
    MAX_NEWS_ITEMS = 18
    MAX_NEWS_ITEMS_BIG = 30
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    BLOOMBERG_RSS_URL = "https://feeds.bloomberg.com/news.rss"
    CNBC_RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    FOX_BUSINESS_RSS_URL = "https://moxie.foxbusiness.com/google-publisher/latest.xml"
    MIT_TECH_REVIEW_RSS_URL = "https://www.technologyreview.com/feed"
    REUTERS_RSS_URL = "https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US%3Aen"

    google_news_items = []
    google_news_last_updated = None
    google_news_items, google_news_last_updated = parse_rss_feed(GOOGLE_NEWS_RSS_URL)
    print(f"Fetched {len(google_news_items)} items from Google News.")

    bloomberg_items = []
    bloomberg_last_updated = None
    bloomberg_items, bloomberg_last_updated = parse_rss_feed(BLOOMBERG_RSS_URL)
    print(f"Fetched {len(bloomberg_items)} items from Bloomberg.")

    cnbc_items = []
    cnbc_last_updated = None
    cnbc_items, cnbc_last_updated = parse_rss_feed(CNBC_RSS_URL)
    print(f"Fetched {len(cnbc_items)} items from CNBC.")

    fox_business_items = []
    fox_business_last_updated = None
    fox_business_items, fox_business_last_updated = parse_rss_feed(FOX_BUSINESS_RSS_URL)
    print(f"Fetched {len(fox_business_items)} items from Fox Business.")

    mit_tech_review_items = []
    mit_tech_review_last_updated = None
    mit_tech_review_items, mit_tech_review_last_updated = parse_rss_feed(MIT_TECH_REVIEW_RSS_URL)
    print(f"Fetched {len(mit_tech_review_items)} items from MIT Technology Review.")

    reuters_items = []
    reuters_last_updated = None
    reuters_items, reuters_last_updated = parse_rss_feed(REUTERS_RSS_URL)
    print(f"Fetched {len(reuters_items)} items from Reuters.")

    # Prepare the output directory
    os.makedirs("output", exist_ok=True)
    shutil.copy("assets/style.css", "output/style.css")

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Top News</title>
        <link rel=\"stylesheet\" href=\"style.css\">
    </head>
    <body>
        <a href="business.html">Business News</a>
        <h2><a href="https://news.google.com/home?hl=en-US&gl=US&ceid=US:en">Google News</a></h2>
        <p class="last-updated">{google_news_last_updated if google_news_last_updated else ''}</p>
        <ul>\n"""

    # build the Google News section with secondary sources
    for item in google_news_items[:MAX_NEWS_ITEMS_BIG]:
        item_description = item.get("description", "")
        item_description_stripped = item_description.replace('<ol>', '').replace('</ol>', '').replace('<li><a href="', '')
        item_description_stripped_split = item_description_stripped.split("</font></li>")
        if len(item_description_stripped_split) > 1:
            # drop the last element which is empty after the rsplit
            item_description_stripped_split = item_description_stripped_split[:-1]
            # drop the first item which is the primary source
            item_description_stripped_split = item_description_stripped_split[1:]
        
        item_secondary_sources_anchors = []

        for source in item_description_stripped_split:
            # URL then '" target="_blank">' then '</a>&nbsp;&nbsp;<font color="#6f6f6f">' then source
            source_url_split = source.split('" target="_blank">')
            if len(source_url_split) != 2:
                print(f"Unexpected source format: {source}")
                continue
            source_url = source_url_split[0]
            source_title_and_publisher_split = source_url_split[1].split('</a>&nbsp;&nbsp;<font color="#6f6f6f">')
            if len(source_title_and_publisher_split) != 2:
                print(f"Unexpected source title and publisher format: {source}")
                continue
            source_title = source_title_and_publisher_split[0]
            source_publisher = source_title_and_publisher_split[1]
            item_secondary_sources_anchors.append(f'<a href="{source_url}" title="{source_title}" target="_blank">[{source_publisher}]</a>')

        if item_secondary_sources_anchors:
            html += f"            <li><a href=\"{item['link']}\" title=\"{item['title']}\" target=\"_blank\"><strong>{item['title']}</strong></a><br>{' '.join(item_secondary_sources_anchors)}</li>\n"
        else:
            html += f"            <li><a href=\"{item['link']}\" title=\"{item['title']}\" target=\"_blank\">{item['title']}</a></li>\n"
    html += "        </ul>\n"

    # build the MIT Technology Review News section
    html += f"""        <h2><a href="https://www.technologyreview.com/">MIT Technology Review</a></h2>
        <p class="last-updated">{mit_tech_review_last_updated if mit_tech_review_last_updated else ''}</p>
        <ul>\n"""
    for item in mit_tech_review_items[:MAX_NEWS_ITEMS]:
        html += f"            <li><a href=\"{item['link']}\" title=\"{item['description']}\" target=\"_blank\"><strong>{item['title']}</strong><br>{item['description']}</a></li>\n"
    html += "        </ul>\n"

    # build the Reuters News section
    html += f"""        <h2><a href="https://www.reuters.com/">Reuters</a></h2>
        <p class="last-updated">{reuters_last_updated if reuters_last_updated else ''}</p>
        <ul>\n"""
    for item in reuters_items[:MAX_NEWS_ITEMS_BIG]:
        # remove ' - Reuters' from the title
        if item['title'].endswith(" [Reuters]"):
            item['title'] = item['title'][:-11]
        html += f"            <li><a href=\"{item['link']}\" target=\"_blank\"><strong>{item['title']}</strong></a></li>\n"
    html += """        </ul>
    </body>
</html>\n"""

    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("index.html generated.")

    html_business = f"""<!DOCTYPE html>
<html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <title>Business News</title>
        <link rel=\"stylesheet\" href=\"style.css\">
    </head>
    <body>
        <a href="index.html">Top News</a>
        <h2><a href="https://www.bloomberg.com/">Bloomberg</a></h2>
        <p class="last-updated">{bloomberg_last_updated if bloomberg_last_updated else ''}</p>
        <ul>\n"""
    for item in bloomberg_items[:MAX_NEWS_ITEMS]:
        html_business += f"            <li><a href=\"{item['link']}\" title=\"{item['description']}\" target=\"_blank\"><strong>{item['title']}</strong><br>{item['description']}</a></li>\n"
    html_business += "        </ul>\n"

    # build the CNBC News section
    html_business += f"""        <h2><a href="https://www.cnbc.com/">CNBC</a></h2>
        <p class="last-updated">{cnbc_last_updated if cnbc_last_updated else ''}</p>
        <ul>\n"""
    for item in cnbc_items[:MAX_NEWS_ITEMS]:
        html_business += f"            <li><a href=\"{item['link']}\" title=\"{item['description']}\" target=\"_blank\"><strong>{item['title']}</strong><br>{item['description']}</a></li>\n"
    html_business += "        </ul>\n"

    # build the Fox Business News section
    html_business += f"""        <h2><a href="https://www.foxbusiness.com/">Fox Business</a></h2>
        <p class="last-updated">{fox_business_last_updated if fox_business_last_updated else ''}</p>
        <ul>\n"""
    for item in fox_business_items[:MAX_NEWS_ITEMS]:
        html_business += f"            <li><a href=\"{item['link']}\" title=\"{item['description']}\" target=\"_blank\"><strong>{item['title']}</strong><br>{item['description']}</a></li>\n"
    html_business += """        </ul>
    </body>
</html>\n"""

    with open("output/business.html", "w", encoding="utf-8") as f:
        f.write(html_business)
    print("business.html generated.")

if __name__ == "__main__":
    generate_news_html()
