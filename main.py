"""
TECH WORLD DAILY INTELLIGENCE → Google Drive

Pipeline:
  1. Pull deep global technology, AI, semiconductor, and startup news from NewsAPI.
  2. Ask Gemini to curate the exact executive-level "TECH WORLD DAILY INTELLIGENCE" report.
  3. Extract topic anchors and construct exact filename: YYYY-MM-DD [Tech] — Topic 1, Topic 2 & Topic 3
  4. Upload formatted result into Google Drive folder via Webhook.

All secrets are read from environment variables — never hardcode keys here.
"""

import os
import sys
import re
import datetime
import requests
import time

# ---------------------------------------------------------------------------
# Config (from environment / GitHub Actions secrets)
# ---------------------------------------------------------------------------
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DRIVE_WEBHOOK_URL = os.environ.get("DRIVE_WEBHOOK_URL", "")

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


# ---------------------------------------------------------------------------
# Step 1: Fetch comprehensive news across global tech & India ecosystem
# ---------------------------------------------------------------------------
def fetch_news() -> list[dict]:
    articles = []
    headers = {"X-Api-Key": NEWS_API_KEY}

    # 1. Global top technology headlines
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"category": "technology", "language": "en", "pageSize": 30}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.ok:
            articles.extend(resp.json().get("articles", []))
    except Exception as e:
        print("Warning fetching top headlines:", e)

    # 1.5. India-centric tech headlines
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"country": "in", "category": "technology", "pageSize": 30}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.ok:
            articles.extend(resp.json().get("articles", []))
    except Exception as e:
        print("Warning fetching India headlines:", e)

    # 2. Deep search for AI, semiconductors, quantum, startups, infrastructure, India tech
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "AI OR semiconductor OR Nvidia OR OpenAI OR Anthropic OR 'Google DeepMind' OR 'Meta AI' OR quantum OR startup OR IndiaAI OR Semicon OR cybersecurity",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
        }
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.ok:
            articles.extend(resp.json().get("articles", []))
    except Exception as e:
        print("Warning fetching everything query:", e)

    # Deduplicate articles
    seen_titles = set()
    unique_articles = []
    for a in articles:
        title = (a.get("title") or "").strip()
        if title and title.lower() not in seen_titles and "[removed]" not in title.lower():
            seen_titles.add(title.lower())
            unique_articles.append(a)

    return unique_articles


# ---------------------------------------------------------------------------
# Step 2: Author the exact "TECH WORLD DAILY INTELLIGENCE" with Gemini
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

    prompt = f"""You are a sharp Indian tech analyst writing "TECH WORLD DAILY INTELLIGENCE" — a daily briefing for Anurag, a tech enthusiast in India who follows AI, big-tech moves, and startups closely.

Date of Briefing: {today_str}

Write the ENTIRE briefing in HINGLISH (Roman Hindi mixed with English) — the way a knowledgeable friend texts: seedhi baat, no jargon, thoda witty. Not formal English, not pure Hindi.

Pick the 6-8 MOST RELEVANT tech stories from the last 24 hours in the raw news stream below. Prioritize in this order:
1. Big announcements from OpenAI, Meta, Google, Apple, Microsoft, Anthropic (CEO-level moves, new models, agent/AI products)
2. AI breakthroughs and research (new models, benchmarks, notable papers)
3. India tech: startup funding rounds, AI policy, semiconductors, IndiaAI mission
4. Major product launches and infrastructure moves (chips, data centers, devices)

For EACH story give all four fields:
- A bold, concrete headline carrying the key numbers/names
- "Kya hua:" 2-3 lines with exact facts — names, numbers, dates, what was announced or launched
- "Background:" 1 line of context (what led to this, if needed)
- "Kyun matter karta hai:" 1-2 lines on why it matters — industry impact, and the India angle wherever one exists
- "Source:" the source name with its URL taken from the raw stream

Rules:
- Every story MUST carry its source link from the raw stream. Never invent or guess a URL.
- Skip pure rumor-mill speculation unless a second source in the stream confirms it.
- If the raw stream is thin in some category, say so in one line instead of padding with filler.
- Keep the "Topic:" line exactly as specified below — it is parsed for the file name.

MANDATORY OUTPUT FORMAT:

🌐 TECH WORLD DAILY INTELLIGENCE
Date: {today_str}
Topic: [3-4 major narrative anchors, comma-separated]

**1. [Headline with key numbers/names]**
Kya hua: [...]
Background: [...]
Kyun matter karta hai: [...]
Source: [Name](URL)

**2. [Headline]**
Kya hua: [...]
Background: [...]
Kyun matter karta hai: [...]
Source: [Name](URL)

(continue the same structure for 6-8 stories total)

💡 Aaj ki ek baat: [1-2 sharp lines capturing the day's biggest shift]

---
Raw News Stream:
{articles_block}

"""

    models_to_try = [GEMINI_MODEL]
    for m in ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-2.5-flash"]:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model_name in models_to_try:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent"
        )
        print(f"Calling Gemini model '{model_name}'...")
        
        max_retries = 3
        delay = 5
        
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    endpoint,
                    headers={
                        "x-goog-api-key": GEMINI_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.25}
                    },
                    timeout=150,
                )
            except requests.exceptions.RequestException as e:
                print(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                last_error = e
                break

            if resp.status_code in (429, 500, 503):
                if attempt < max_retries:
                    print(f"Server busy (status {resp.status_code}), retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                    continue

            if resp.status_code != 200:
                print(f"Gemini API returned status {resp.status_code} for model '{model_name}': {resp.text}")
                last_error = requests.exceptions.HTTPError(
                    f"{resp.status_code} Client Error for model {model_name}: {resp.text}",
                    response=resp
                )
                break  # try next fallback model

            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as err:
                print(f"Unexpected response structure: {data}")
                last_error = err
                break

    if last_error:
        raise last_error
    raise RuntimeError("Failed to generate content with Gemini.")


# ---------------------------------------------------------------------------
# Step 3: Extract Topic and Format File Name
# Format: YYYY-MM-DD [Tech] — Topic 1, Topic 2 & Topic 3
# ---------------------------------------------------------------------------
def generate_file_name(report_text: str) -> str:
    today_iso = datetime.date.today().strftime("%Y-%m-%d")
    
    # Try to extract Topic line from report
    topic_match = re.search(r"Topic:\s*([^\n\r]+)", report_text, re.IGNORECASE)
    if topic_match:
        topic = topic_match.group(1).strip()
        # Clean up unwanted markdown bold or brackets
        topic = re.sub(r"[\*\[\]#]", "", topic).strip()
        # Truncate if overly long
        if len(topic) > 75:
            topic = topic[:72] + "..."
        return f"{today_iso} [Tech] \u2014 {topic}"
    
    return f"{today_iso} [Tech] \u2014 Daily Intelligence Briefing"


# ---------------------------------------------------------------------------
# Step 4: Upload to Google Drive via Google Apps Script Webhook
# ---------------------------------------------------------------------------
def upload_to_drive(markdown_text: str) -> dict:
    doc_title = generate_file_name(markdown_text)
    print(f"Generated Document Title: {doc_title}")

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
    missing = [k for k, v in [("NEWS_API_KEY", NEWS_API_KEY), 
                              ("GEMINI_API_KEY", GEMINI_API_KEY), 
                              ("DRIVE_WEBHOOK_URL", DRIVE_WEBHOOK_URL)] if not v]
    if missing:
        print(f"Error: Missing required environment variable(s): {', '.join(missing)}")
        print("Please configure them in your local environment or as GitHub Repository Secrets.")
        sys.exit(1)

    print("Fetching latest comprehensive tech news...")
    articles = fetch_news()
    if not articles:
        print("No articles returned by NewsAPI today — nothing to upload.")
        sys.exit(0)
    print(f"Fetched {len(articles)} unique articles.")

    print("Authoring 'TECH WORLD DAILY INTELLIGENCE' with Gemini...")
    briefing = summarize_with_gemini(articles)

    print("Uploading styled executive briefing to Google Drive...")
    result = upload_to_drive(briefing)

    print(f"Done! Created document -> {result.get('url', 'Uploaded')}")


if __name__ == "__main__":
    main()
