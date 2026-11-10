from datetime import datetime, timedelta, timezone
import feedparser

FEEDS = {
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "MIT Technology Review": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "OpenAI": "https://openai.com/news/rss.xml",
}


def fetch_feed(source: str, url: str, hours: int = 24) -> list[dict]:
    """Return items from one feed published within the last `hours` hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    parsed = feedparser.parse(url)

    if parsed.bozo and not parsed.entries:
        print(f"[warn] could not read feed: {source}")
        return []

    items = []
    for entry in parsed.entries:
        t = entry.get("published_parsed") or entry.get("updated_parsed")
        if not t:
            continue
        published = datetime(*t[:6], tzinfo=timezone.utc)
        if published >= cutoff:
            items.append({
                "source": source,
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": published.isoformat(),
                "summary": entry.get("summary", "")[:500],
            })
    return items


def fetch_all_recent(hours: int = 24) -> list[dict]:
    """Collect recent items from every feed, newest first."""
    all_items = []
    for source, url in FEEDS.items():
        all_items.extend(fetch_feed(source, url, hours))
    return sorted(all_items, key=lambda x: x["published"], reverse=True)


if __name__ == "__main__":
    items = fetch_all_recent()
    print(f"Found {len(items)} items in the last 24 hours\n")
    for item in items:
        print(f"[{item['source']}] {item['title']}")
        print(f"  {item['link']}\n")