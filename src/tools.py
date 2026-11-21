import json
import requests
from bs4 import BeautifulSoup
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

def read_article(url: str, max_chars: int = 4000) -> dict:
    """Fetch a page and return the start of its main text."""
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (ai-news-agent learning project)"},
        timeout=10,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if len(p) > 40)
    return {"url": url, "text": text[:max_chars]}


TOOLS = [
    {
        "name": "fetch_recent_ai_news",
        "description": (
            "Fetch AI news articles published recently from major tech blogs and "
            "news sites (TechCrunch, The Verge, MIT Technology Review, OpenAI, "
            "Hugging Face). Returns a list of items, each with source, title, "
            "link, published time, and a short summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to look. Defaults to 24.",
                    "minimum": 1,
                    "maximum": 72,
                }
            },
            "required": [],
        },
    },
    {
        "name": "read_article",
        "description": (
            "Fetch and read the main text of one article, given its URL (use links "
            "returned by fetch_recent_ai_news). Use this when a headline looks "
            "important and you need details beyond the short summary. Returns the "
            "first part of the article text, or an error if the page can't be read."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full article URL."}
            },
            "required": ["url"],
        },
    },
]

TOOL_FUNCTIONS = {
    "fetch_recent_ai_news": fetch_all_recent,
    "read_article": read_article,
}


def run_tool(name: str, tool_input: dict) -> str:
    """Dispatcher: run the named tool and always return a JSON string."""
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return json.dumps(func(**tool_input))
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    items = fetch_all_recent()
    print(f"Found {len(items)} items in the last 24 hours\n")
    for item in items:
        print(f"[{item['source']}] {item['title']}")
        print(f"  {item['link']}\n")