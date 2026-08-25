"""
Daily Tech News Briefing → Google Drive

Pipeline:
  1. Pull the latest technology headlines from NewsAPI.
  2. Ask Gemini to filter/summarize them into a clean briefing.
  3. Upload the result as a Google Doc directly into your Google Drive folder via Webhook.

All secrets are read from environment variables — never hardcode keys here.
"""

import os
import sys
import datetime
import requests

# ---------------------------------------------------------------------------
# Config (from environment / GitHub Actions secrets)
# ---------------------------------------------------------------------------
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DRIVE_WEBHOOK_URL = os.environ["DRIVE_WEBHOOK_URL"]

GEMINI_MODEL = "gemini-3.6-flash"

# Tweak this to change what counts as "relevant" news.
NEWS_QUERY_PARAMS = {
    "category": "technology",
    "language": "en",
    "pageSize": 25,
}


# ---------------------------------------------------------------------------
# Step 1: Fetch news
# ---------------------------------------------------------------------------
def fetch_news() -> list[dict]:
    url = "https://newsapi.org/v2/top-headlines"
    params = {**NEWS_QUERY_PARAMS, "apiKey": NEWS_API_KEY}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    articles = data.get("articles", [])
    if not articles:
        # Fallback: NewsAPI's top-headlines "technology" category is
        # sometimes thin, so widen the net with a keyword search.
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "technology OR AI OR software OR startup",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 25,
            "apiKey": NEWS_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    return articles


# ---------------------------------------------------------------------------
# Step 2: Summarize / curate with Gemini
# ---------------------------------------------------------------------------
def summarize_with_gemini(articles: list[dict]) -> str:
    lines = []
    for a in articles:
        title = (a.get("title") or "").strip()
        desc = (a.get("description") or "").strip()
        source = ((a.get("source") or {}).get("name") or "").strip()
        url = (a.get("url") or "").strip()
        if not title:
            continue
        lines.append(f"- TITLE: {title}\n  SOURCE: {source}\n  DESC: {desc}\n  URL: {url}")
    articles_block = "\n".join(lines)

    today_str = datetime.date.today().strftime("%B %d, %Y")

    prompt = f"""You are curating a daily technology briefing for a busy professional.

Below is a raw list of today's tech news headlines. Do the following:
1. Remove duplicates and low-value/clickbait items.
2. Group the remaining stories into logical sections (e.g. "AI", "Big Tech",
   "Startups & Funding", "Gadgets", "Other").
3. For each story, write a tight 1-2 sentence summary in your own words.
4. Include the source name and URL for each item so it can be verified.
5. Keep the whole briefing skimmable — a few minutes of reading, not a wall of text.

Title the document "Tech Briefing - {today_str}".

Output clean Markdown (headings, bullet points). Do not add commentary
outside the briefing itself.

Raw articles:
{articles_block}
"""

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    resp = requests.post(
        endpoint,
        params={"key": GEMINI_API_KEY},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ---------------------------------------------------------------------------
# Step 3: Upload to Google Drive via Google Apps Script Webhook
# ---------------------------------------------------------------------------
def upload_to_drive(markdown_text: str) -> dict:
    today_str = datetime.date.today().strftime("%B %d, %Y")
    doc_title = f"Tech Briefing - {today_str}"

    payload = {
        "title": doc_title,
        "content": markdown_text,
    }

    resp = requests.post(DRIVE_WEBHOOK_URL, json=payload, timeout=60)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"url": "Uploaded successfully"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Fetching latest tech news...")
    articles = fetch_news()
    if not articles:
        print("No articles returned by NewsAPI today — nothing to upload.")
        sys.exit(0)
    print(f"Fetched {len(articles)} articles.")

    print("Summarizing with Gemini...")
    briefing = summarize_with_gemini(articles)

    print("Uploading to Google Drive...")
    result = upload_to_drive(briefing)

    print(f"Done! Created document -> {result.get('url', 'Uploaded')}")


if __name__ == "__main__":
    main()
