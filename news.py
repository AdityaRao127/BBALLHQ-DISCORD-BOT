import feedparser
import re
def fetch_feed(feed_urls):
    """Fetches the latest updates from the given RSS feed URLs"""
    updates = []
    for feed_url in feed_urls:
        feed = feedparser.parse(feed_url)
        feed_updates = []
        for entry in feed.entries:
            feed_updates.append({
                'author': entry.author,
                'content': re.sub(r'<[^>]*?>', '', entry.summary),
                'link': entry.link,
                'published': entry.published
            })
        updates.append(feed_updates)
    return updates
