"""
This module fetches news from various RSS feeds and generates HTML pages for different news categories.
It includes functions for parsing RSS feeds, extracting secondary sources, and building HTML content for news pages.
"""
import http
import os
import shutil
import ssl
import urllib.request
import certifi
import feedparser

def parse_rss_feed(url: str):
    """
    Parse an RSS feed from the given URL and return a list of news items and the last updated time.
    Args:
        url (str): The URL of the RSS feed.
    Returns:
        tuple: (list of news items, last updated time)
    """
    context = ssl.create_default_context(cafile=certifi.where())
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    handlers = [urllib.request.HTTPSHandler(context=context)]
    try:
        print(f"Fetching items from {os.path.dirname(url)}")
        feed = feedparser.parse(url, handlers=handlers)
    except http.client.RemoteDisconnected as e:
        print(f"Error: RemoteDisconnected with {url}")
        print(e)
        return [], "N/a"

    feed_title = feed.feed.get('title', 'Unknown feed')
    if feed.bozo:
        print(f"Feed.bozo_exception: {feed.bozo_exception}  for URL: {url}")
    print(f"Loading {len(feed.entries)} items from {feed_title}")
    items = []
    for entry in feed.entries:
        entry_title = entry.get("title", "No title")
        entry_title = entry_title.replace("<strong>", "").replace("</strong>", "")
        # Google News formats titles like "Headline - Source"
        entry_title_rsplit = entry_title.rsplit(" - ", 1)
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


def extract_secondary_sources_from_description(description: str):
    """
    Extract secondary news sources from the description HTML of a Google News item.
    Args:
        description (str): The HTML description containing secondary sources.
    Returns:
        list: List of HTML anchor tags for secondary sources.
    """
    description_stripped = description.replace('<li><a href="', '')
    description_stripped = description_stripped.replace('<ol>', '').replace('</ol>', '')
    description_stripped = description_stripped.replace('<strong>', '').replace('</strong>', '')
    sources_split_pattern = "</font></li>"
    description_stripped_split = description_stripped.split(sources_split_pattern)

    if len(description_stripped_split) > 1:
        # drop the first item which is the primary source
        description_stripped_split = description_stripped_split[1:]
        # drop the last element which is empty after the rsplit
        description_stripped_split = description_stripped_split[:-1]
    else:
        return []

    item_secondary_sources_anchors = []
    for source in description_stripped_split:
        # URL then '" target="_blank">' then '</a>&nbsp;&nbsp;<font color="#6f6f6f">' then source
        url_split_pattern = '" target="_blank">'
        url_split = source.split(url_split_pattern)
        if len(url_split) != 2:
            print(f"Unexpected source format during url split: {source}")
            continue
        url = url_split[0]
        title_publisher_split_pattern = '</a>&nbsp;&nbsp;<font color="#6f6f6f">'
        title_publisher_split = url_split[1].split(title_publisher_split_pattern)
        if len(title_publisher_split) != 2:
            print(f"Unexpected source format during title-publisher split: {source}")
            continue
        title = title_publisher_split[0]
        publisher = title_publisher_split[1]
        item_secondary_sources_anchors.append(
            f'<a href="{url}" title="{title}" target="_blank">[{publisher}]</a>'
        )

    return item_secondary_sources_anchors


def generate_html_base(title: str):
    """
    Generate the base HTML structure for a news page with the given title.
    Args:
        title (str): The title of the HTML page.
    Returns:
        str: The base HTML string.
    """
    html_base = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel=\"stylesheet\" href=\"style.css\">
</head>
<body>\n"""
    return html_base


def generate_html_closing():
    """
    Generate the closing HTML tags for a news page.
    Returns:
        str: The closing HTML string.
    """
    html_closing = """    </body>
    <footer>
        <p>Author: David C. Backer</p>
        <p><a href="https://github.com/davidcbacker/news">Source code</a></p>
    </footer>
</html>\n"""
    return html_closing


def generate_top_nav_bar(current_page: str):
    """
    Generate the top navigation bar for the news pages.
    Args:
        current_page (str): The filename of the current page to highlight.
    Returns:
        str: The HTML for the navigation bar.
    """
    pages = [
        ("index.html", "Top News"),
        ("us.html", "U.S. News"),
        ("world.html", "World News"),
        ("business.html", "Business"),
        ("security.html", "Security"),
        ("technology.html", "Technology")
    ]
    nav_bar = "        <ul class=\"navbar\">\n"
    for page_file, page_name in pages:
        if page_file == current_page:
            nav_bar += f"            <li class=\"active\"><a href=\"{page_file}\">{page_name}</a></li>\n"
            # nav_bar += f"            <li><a class=\"active\" href=\"{page_file}\"><{page_name}</a></li>\n"
        else:
            nav_bar += f"            <li><a href=\"{page_file}\">{page_name}</a></li>\n"
    nav_bar += "        </ul>\n"
    return nav_bar


def generate_google_news_html_section(section_title, section_url, google_news_items, google_news_last_updated, max_news_items):
    """
    Generate the HTML section for Google News items.
    Args:
        google_news_items (list): List of Google News items.
        google_news_last_updated (str): Last updated time for Google News.
        max_news_items (int): Maximum number of news items to display.
    Returns:
        str: The HTML section for Google News.
    """
    google_news_html = f"""        <h2 id="{section_title.lower().replace(' ', '-').replace('.', '')}"><a href="{section_url}">{section_title}</a></h2>
        <p class="last-updated">{google_news_last_updated if google_news_last_updated else ''}</p>
        <ul class=\"news-list\">\n"""
    for item in google_news_items[:max_news_items]:
        item_description = item.get("description", "")
        item_secondary_sources_anchors = extract_secondary_sources_from_description(item_description)

        if item_secondary_sources_anchors:
            google_news_html += f"            <li><a href=\"{item['link']}\" title=\"{item['title']}\" target=\"_blank\"><strong>{item['title']}</strong></a> {' '.join(item_secondary_sources_anchors)}</li>\n"
        else:
            google_news_html += f"            <li><a href=\"{item['link']}\" title=\"{item['title']}\" target=\"_blank\"><strong>{item['title']}</strong></a></li>\n"
    google_news_html += "        </ul>\n"
    return google_news_html


def generate_reuters_html_section(section_title, section_url, reuters_items, reuters_last_updated, max_news_items):
    """
    Generate the HTML section for Reuters news items.
    Args:
        section_title (str): The title of the Reuters news section.
        section_url (str): The URL of the Reuters news source.
        reuters_items (list): List of Reuters news items.
        reuters_last_updated (str): Last updated time for Reuters news.
        max_news_items (int): Maximum number of news items to display.
    Returns:
        str: The HTML section for Reuters news.
    """
    reuters_html = f"""        <h2 id="reuters"><a href="{section_url}">{section_title}</a></h2>
        <p class="last-updated">{reuters_last_updated if reuters_last_updated else ''}</p>
        <ul class=\"news-list\">\n"""
    for item in reuters_items[:max_news_items]:
        # remove ' - Reuters' from the title
        if item['title'].endswith(" [Reuters]"):
            item['title'] = item['title'][:-11]
        reuters_html += f"            <li><a href=\"{item['link']}\" target=\"_blank\"><strong>{item['title']}</strong></a></li>\n"
    reuters_html += "        </ul>\n"
    return reuters_html


def generate_reddit_technology_html_section(
    section_title,
    section_url,
    reddit_technology_items,
    reddit_technology_last_updated,
    max_news_items
):
    """
    Generate the HTML section for Reddit Technology news items.
    Args:
        section_title (str): The title of the Reddit Technology news section.
        section_url (str): The URL of the Reddit Technology news source.
        reddit_technology_items (list): List of Reddit Technology news items.
        reddit_technology_last_updated (str): Last updated time for Reddit Technology news.
        max_news_items (int): Maximum number of news items to display.
    """
    reddit_technology_html = f"""        <h2 id="{section_title.lower().replace(' ', '-').replace('.', '')}"><a href="{section_url}">{section_title}</a></h2>
        <p class="last-updated">{reddit_technology_last_updated if reddit_technology_last_updated else ''}</p>
        <ul class=\"news-list\">\n"""
    for item in reddit_technology_items[:max_news_items]:
        reddit_technology_html += f"            <li><a href=\"{item['link']}\" target=\"_blank\"><strong>{item['title']}</strong></a></li>\n"
    reddit_technology_html += "        </ul>\n"
    return reddit_technology_html


def generate_html_section(section_title, section_url, news_items, news_last_updated, max_news_items):
    """
    Generate the HTML section for a generic news source.
    Args:
        section_title (str): The title of the news section.
        section_url (str): The URL of the news source.
        news_items (list): List of news items.
        news_last_updated (str): Last updated time for the news source.
        max_news_items (int): Maximum number of news items to display.
    Returns:
        str: The HTML section for the news source.
    """
    html = f"""        <h2 id="{section_title.lower().replace(' ', '-').replace('.', '')}"><a href="{section_url}">{section_title}</a></h2>
        <p class="last-updated">{news_last_updated if news_last_updated else ''}</p>
        <ul class=\"news-list\">\n"""
    for item in news_items[:max_news_items]:
        html += f"            <li><a href=\"{item['link']}\" title=\"{item['description']}\" target=\"_blank\"><strong>{item['title']}</strong><br>{item['description']}</a></li>\n"
    html += "        </ul>\n"
    return html


def generate_index_html(max_news_items):
    """
    Generate the HTML for the index (Top News) page.
    Args:
        max_news_items (int): Maximum number of news items to display per section.
    Returns:
        str: The complete HTML for the index page.
    """
    google_news_rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    google_news_items = []
    google_news_last_updated = None
    google_news_items, google_news_last_updated = parse_rss_feed(google_news_rss_url)
    print(f"Loaded {len(google_news_items)} items from Google News.")

    reuters_rss_url = "https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US%3Aen"
    reuters_items = []
    reuters_last_updated = None
    reuters_items, reuters_last_updated = parse_rss_feed(reuters_rss_url)
    print(f"Loaded {len(reuters_items)} items from Reuters.")

    index_html = generate_html_base("Top News")
    index_html += generate_top_nav_bar("index.html")

    index_html += generate_google_news_html_section(
        section_title="Google News",
        section_url="https://news.google.com/home?hl=en-US&gl=US&ceid=US:en",
        google_news_items=google_news_items,
        google_news_last_updated=google_news_last_updated,
        max_news_items=max_news_items
    )

    index_html += generate_reuters_html_section(
        section_title="Reuters",
        section_url="https://www.reuters.com",
        reuters_items=reuters_items,
        reuters_last_updated=reuters_last_updated,
        max_news_items=max_news_items
    )

    index_html += generate_html_closing()
    return index_html


def generate_us_news_html(max_news_items):
    """
    Generate the HTML for the U.S. News page.
    Args:
        max_news_items (int): Maximum number of news items to display per section.
    Returns:
        str: The complete HTML for the U.S. News page.
    """
    google_news_us_rss_url = "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE"
    google_news_us_items = []
    google_news_us_last_updated = None
    google_news_us_items, google_news_us_last_updated = parse_rss_feed(google_news_us_rss_url)
    print(f"Loaded {len(google_news_us_items)} items from Google News US.")

    fox_weather_rss_url = "https://moxie.foxweather.com/google-publisher/latest.xml"
    fox_weather_items = []
    fox_weather_last_updated = None
    fox_weather_items, fox_weather_last_updated = parse_rss_feed(fox_weather_rss_url)
    print(f"Loaded {len(fox_weather_items)} items from Fox Weather.")

    cnbc_us_rss_url = "https://www.cnbc.com/id/15837362/device/rss/rss.html"
    cnbc_us_items = []
    cnbc_us_last_updated = None
    cnbc_us_items, cnbc_us_last_updated = parse_rss_feed(cnbc_us_rss_url)
    print(f"Loaded {len(cnbc_us_items)} items from CNBC U.S.")

    cnn_us_rss_url = "http://rss.cnn.com/rss/cnn_us.rss"
    cnn_us_items = []
    cnn_us_last_updated = None
    cnn_us_items, cnn_us_last_updated = parse_rss_feed(cnn_us_rss_url)
    print(f"Loaded {len(cnn_us_items)} items from CNN U.S.")

    us_news_html = generate_html_base("U.S. News")
    us_news_html += generate_top_nav_bar("us.html")

    us_news_html += generate_google_news_html_section(
        section_title="Google News - U.S.",
        section_url="https://news.google.com/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE",
        google_news_items=google_news_us_items,
        google_news_last_updated=google_news_us_last_updated,
        max_news_items=max_news_items
    )

    us_news_html += generate_html_section(
        section_title="Fox Weather",
        section_url="https://www.foxweather.com/",
        news_items=fox_weather_items,
        news_last_updated=fox_weather_last_updated,
        max_news_items=max_news_items
    )

    us_news_html += generate_html_section(
        section_title="CNBC U.S.",
        section_url="https://www.cnbc.com/us-news/",
        news_items=cnbc_us_items,
        news_last_updated=cnbc_us_last_updated,
        max_news_items=max_news_items
    )

    us_news_html += generate_html_section(
        section_title="CNN U.S.",
        section_url="https://www.cnn.com/us",
        news_items=cnn_us_items,
        news_last_updated=cnn_us_last_updated,
        max_news_items=max_news_items
    )

    us_news_html += generate_html_closing()
    return us_news_html

def generate_world_news_html(max_news_items):
    """
    Generate the HTML for the World News page.
    Args:
        max_news_items (int): Maximum number of news items to display.
    Returns:
        str: The complete HTML for the World News page.
    """
    google_news_world_rss_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB"
    google_news_world_items = []
    google_news_world_last_updated = None
    google_news_world_items, google_news_world_last_updated = parse_rss_feed(google_news_world_rss_url)
    print(f"Loaded {len(google_news_world_items)} items from Google News World.")

    world_news_html = generate_html_base("World News")
    world_news_html += generate_top_nav_bar("world.html")

    bbc_world_rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
    bbc_world_items = []
    bbc_world_last_updated = None
    bbc_world_items, bbc_world_last_updated = parse_rss_feed(bbc_world_rss_url)
    print(f"Loaded {len(bbc_world_items)} items from BBC World.")

    world_news_html += generate_google_news_html_section(
        section_title="Google News - World",
        section_url="https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
        google_news_items=google_news_world_items,
        google_news_last_updated=google_news_world_last_updated,
        max_news_items=max_news_items
    )

    world_news_html += generate_html_section(
        section_title="BBC News - World",
        section_url="https://www.bbc.com/news/world",
        news_items=bbc_world_items,
        news_last_updated=bbc_world_last_updated,
        max_news_items=max_news_items
    )

    world_news_html += generate_html_closing()
    return world_news_html

def generate_business_html(max_news_items):
    """
    Generate the HTML for the Business News page.
    Args:
        max_news_items (int): Maximum number of news items to display per section.
    Returns:
        str: The complete HTML for the Business News page.
    """

    google_news_business_rss_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB"
    google_news_business_items = []
    google_news_business_last_updated = None
    google_news_business_items, google_news_business_last_updated = parse_rss_feed(google_news_business_rss_url)
    print(f"Loaded {len(google_news_business_items)} items from Google News Business.")

    bloomberg_rss_url = "https://feeds.bloomberg.com/news.rss"
    bloomberg_items = []
    bloomberg_last_updated = None
    bloomberg_items, bloomberg_last_updated = parse_rss_feed(bloomberg_rss_url)
    print(f"Loaded {len(bloomberg_items)} items from Bloomberg.")

    cnbc_rss_url = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    cnbc_items = []
    cnbc_last_updated = None
    cnbc_items, cnbc_last_updated = parse_rss_feed(cnbc_rss_url)
    print(f"Loaded {len(cnbc_items)} items from CNBC.")

    fox_business_rss_url = "https://moxie.foxbusiness.com/google-publisher/latest.xml"
    fox_business_items = []
    fox_business_last_updated = None
    fox_business_items, fox_business_last_updated = parse_rss_feed(fox_business_rss_url)
    print(f"Loaded {len(fox_business_items)} items from Fox Business.")

    business_html = generate_html_base("Business")
    business_html += generate_top_nav_bar("business.html")

    business_html += generate_google_news_html_section(
        section_title="Google News - Business",
        section_url="https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
        google_news_items=google_news_business_items,
        google_news_last_updated=google_news_business_last_updated,
        max_news_items=max_news_items
    )

    business_html += generate_html_section(
        section_title="Bloomberg",
        section_url="https://www.bloomberg.com/",
        news_items=bloomberg_items,
        news_last_updated=bloomberg_last_updated,
        max_news_items=max_news_items
    )

    business_html += generate_html_section(
        section_title="CNBC",
        section_url="https://www.cnbc.com/",
        news_items=cnbc_items,
        news_last_updated=cnbc_last_updated,
        max_news_items=max_news_items
    )

    business_html += generate_html_section(
        section_title="Fox Business",
        section_url="https://www.foxbusiness.com/",
        news_items=fox_business_items,
        news_last_updated=fox_business_last_updated,
        max_news_items=max_news_items
    )

    business_html += generate_html_closing()
    return business_html


def generate_security_html(max_news_items):
    """
    Generate the HTML for the Security News page.
    Args:
        max_news_items (int): Maximum number of news items to display per section.
    Returns:
        str: The complete HTML for the Security News page.
    """

    talkback_news_rss_url = "https://talkback.sh/resources/feed/news/"
    talkback_news_items = []
    talkback_news_last_updated = None
    talkback_news_items, talkback_news_last_updated = parse_rss_feed(talkback_news_rss_url)

    talkback_technical_rss_url = "https://talkback.sh/resources/feed/tech/"
    talkback_technical_items = []
    talkback_technical_last_updated = None
    talkback_technical_items, talkback_technical_last_updated = parse_rss_feed(talkback_technical_rss_url)

    hacker_news_rss_url = "https://feeds.feedburner.com/TheHackersNews"
    hacker_news_items = []
    hacker_news_last_updated = None
    hacker_news_items, hacker_news_last_updated = parse_rss_feed(hacker_news_rss_url)
    print(f"Loaded {len(hacker_news_items)} items from Hacker News.")

    sans_internet_storm_center_rss_url = "https://isc.sans.edu/rssfeed.xml"
    sans_isc_items = []
    sans_isc_last_updated = None
    sans_isc_items, sans_isc_last_updated = parse_rss_feed(sans_internet_storm_center_rss_url)
    print(f"Loaded {len(sans_isc_items)} items from SANS Internet Storm Center.")

    krebs_on_security_rss_url = "https://krebsonsecurity.com/feed/"
    krebs_items = []
    krebs_last_updated = None
    krebs_items, krebs_last_updated = parse_rss_feed(krebs_on_security_rss_url)
    print(f"Loaded {len(krebs_items)} items from Krebs on Security.")

    security_html = generate_html_base("Security")
    security_html += generate_top_nav_bar("security.html")

    security_html += generate_html_section(
        section_title="Talkback.sh News",
        section_url="https://talkback.sh/",
        news_items=talkback_news_items,
        news_last_updated=talkback_news_last_updated,
        max_news_items=max_news_items
    )

    security_html += generate_html_section(
        section_title="Talkback.sh Technical",
        section_url="https://talkback.sh/",
        news_items=talkback_technical_items,
        news_last_updated=talkback_technical_last_updated,
        max_news_items=max_news_items
    )

    security_html += generate_html_section(
        section_title="Hacker News",
        section_url="https://thehackernews.com/",
        news_items=hacker_news_items,
        news_last_updated=hacker_news_last_updated,
        max_news_items=max_news_items
    )

    security_html += generate_html_section(
        section_title="SANS Internet Storm Center",
        section_url="https://isc.sans.edu/",
        news_items=sans_isc_items,
        news_last_updated=sans_isc_last_updated,
        max_news_items=max_news_items
    )

    security_html += generate_html_section(
        section_title="Krebs on Security",
        section_url="https://krebsonsecurity.com/",
        news_items=krebs_items,
        news_last_updated=krebs_last_updated,
        max_news_items=max_news_items
    )

    security_html += generate_html_closing()
    return security_html


def generate_technology_html(max_news_items):
    """
    Generate the HTML for the Technology News page.
    Args:
        max_news_items (int): Maximum number of news items to display per section.
    Returns:
        str: The complete HTML for the Technology News page.
    """
    google_news_technology_rss_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB"
    google_news_technology_items = []
    google_news_technology_last_updated = None
    google_news_technology_items, google_news_technology_last_updated = parse_rss_feed(google_news_technology_rss_url)
    print(f"Loaded {len(google_news_technology_items)} items from Google News Technology.")

    mit_tech_review_rss_url = "https://www.technologyreview.com/feed"
    mit_tech_review_items = []
    mit_tech_review_last_updated = None
    mit_tech_review_items, mit_tech_review_last_updated = parse_rss_feed(mit_tech_review_rss_url)
    print(f"Loaded {len(mit_tech_review_items)} items from MIT Technology Review.")

    reddit_technology_rss_url = "https://www.reddit.com/r/technology/top/.rss?t=month"
    reddit_technology_items = []
    reddit_technology_last_updated = None
    reddit_technology_items, reddit_technology_last_updated = parse_rss_feed(reddit_technology_rss_url)
    print(f"Loaded {len(reddit_technology_items)} items from Reddit Technology.")

    technology_html = generate_html_base("Technology")
    technology_html += generate_top_nav_bar("technology.html")

    technology_html += generate_google_news_html_section(
        section_title="Google News - Technology",
        section_url="https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        google_news_items=google_news_technology_items,
        google_news_last_updated=google_news_technology_last_updated,
        max_news_items=max_news_items
    )

    technology_html += generate_html_section(
        section_title="MIT Technology Review",
        section_url="https://www.technologyreview.com/",
        news_items=mit_tech_review_items,
        news_last_updated=mit_tech_review_last_updated,
        max_news_items=max_news_items
    )

    technology_html += generate_reddit_technology_html_section(
        section_title="Reddit Technology",
        section_url="https://www.reddit.com/r/technology/",
        reddit_technology_items=reddit_technology_items,
        reddit_technology_last_updated=reddit_technology_last_updated,
        max_news_items=max_news_items
    )

    technology_html += generate_html_closing()
    return technology_html

def write_content_to_file(content: str, filename: str):
    """
    Write the given content to a file with the specified filename.
    Args:
        content (str): The content to write to the file.
        filename (str): The name of the file to write to.
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {filename}.")

def generate_news_pages():
    """
    Generate all news HTML pages and write them to the output directory.
    """
    max_news_items = 18
    max_news_items_small = 10
    max_news_items_big = 30

    # Prepare the output directory
    os.makedirs("output", exist_ok=True)
    shutil.copy("assets/style.css", "output/style.css")

    index_html = generate_index_html(max_news_items=max_news_items_big)
    write_content_to_file(index_html, "output/index.html")

    us_news_html = generate_us_news_html(max_news_items=max_news_items)
    write_content_to_file(us_news_html, "output/us.html")

    world_news_html = generate_world_news_html(max_news_items=max_news_items_big)
    write_content_to_file(world_news_html, "output/world.html")

    business_html = generate_business_html(max_news_items=max_news_items_small)
    write_content_to_file(business_html, "output/business.html")

    security_html = generate_security_html(max_news_items=max_news_items_small)
    write_content_to_file(security_html, "output/security.html")

    technology_html = generate_technology_html(max_news_items=max_news_items)
    write_content_to_file(technology_html, "output/technology.html")

if __name__ == "__main__":
    generate_news_pages()
