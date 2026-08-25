"""
Daily Tech News Briefing → Google Drive

Pipeline:
  1. Pull the latest technology headlines and industry news from NewsAPI.
  2. Ask Gemini to curate and structure an executive-level intelligence report.
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


# ---------------------------------------------------------------------------
# Step 1: Fetch comprehensive news
# ---------------------------------------------------------------------------
def fetch_news() -> list[dict]:
    articles = []
    
    # 1. Top tech headlines
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"category": "technology", "language": "en", "pageSize": 30, "apiKey": NEWS_API_KEY}
        resp = requests.get(url, params=params, timeout=30)
        if resp.ok:
            articles.extend(resp.json().get("articles", []))
    except Exception as e:
        print("Warning fetching top headlines:", e)

    # 2. Broader query for AI, semiconductors, startups, big tech, and India tech
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "AI OR semiconductor OR Nvidia OR OpenAI OR Google OR Apple OR startup OR cybersecurity OR India tech",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 40,
            "apiKey": NEWS_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=30)
        if resp.ok:
            articles.extend(resp.json().get("articles", []))
    except Exception as e:
        print("Warning fetching everything query:", e)

    # Deduplicate by title
    seen_titles = set()
    unique_articles = []
    for a in articles:
        title = (a.get("title") or "").strip().lower()
        if title and title not in seen_titles and "[removed]" not in title:
            seen_titles.add(title)
            unique_articles.append(a)

    return unique_articles


# ---------------------------------------------------------------------------
# Step 2: Generate "TECH WORLD DAILY INTELLIGENCE" with Gemini
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

    prompt = f"""You are a world-class technology strategist, Silicon Valley venture capitalist, and chief intelligence officer.
Your task is to analyze today's technology news and author the prestigious "TECH WORLD DAILY INTELLIGENCE" executive briefing.

Date: {today_str}

Analyze the raw news items below and produce an authoritative, highly detailed intelligence document that strictly follows the EXACT format below.

### STRICT FORMAT REQUIREMENTS:

# 🌐 TECH WORLD DAILY INTELLIGENCE
**Date:** {today_str}
**Topic:** [Identify the top 3-4 major themes/stories driving today's briefing separated by commas / ampersands]
**Overall Tech Pulse:** [A comprehensive, high-level strategic paragraph analyzing today's macro shifts, capital allocation, technology transitions, and industry posture.]

---

## 🔥 TOP 5 DEVELOPMENTS

For each of the top 5 most critical industry-defining stories, generate this EXACT structured breakdown:

### 1. [Bold, Punchy, Strategic Headline with Dollar Amounts / Metrics if applicable]
* **Importance:** [e.g., 10/10 (Industry Defining) or 9/10 (High Impact) or 8/10 (High Impact)]
* **Category:** [e.g., Infrastructure & Big Tech Finance / Artificial Intelligence & Open Source / AI Regulation & Governance / Semiconductor Ecosystem & Sovereign AI / AI Cybersecurity & Defense / Big Tech Leadership & Strategy]
* **Verification Status:** 🔴 Confirmed ([Official Release / Official Announcement / Official Transition / Venture Filing / Security Release / etc.])
* **What Happened:** [Detailed 2-3 sentence breakdown of exact details, key entities, numbers, specifications, and actions taken.]
* **Why It Matters:** [Deep strategic, economic, and competitive analysis. Why this alters market dynamics or industry balance.]
* **What Changed:** [Direct comparison of previous paradigm vs the new reality established today.]
* **What's Next:** [Upcoming roadmap, milestones, regulatory deadlines, hardware deployments, or market reactions.]
* **Source:** [Source Name](URL)
* **Independent Coverage:** [Secondary Source Name](URL) [if available from raw list, else omit]

(Repeat identical structure for items 2, 3, 4, and 5)

---

## 🤖 AI RADAR
1. **[Headline/Theme]:** [Concise 1-2 sentence high-impact intelligence summary]. *(Source: [Source Name](URL))*
2. **[Headline/Theme]:** [Concise 1-2 sentence high-impact intelligence summary]. *(Source: [Source Name](URL))*
3. **[Headline/Theme]:** [Concise 1-2 sentence high-impact intelligence summary]. *(Source: [Source Name](URL))*
4. **[Headline/Theme]:** [Concise 1-2 sentence high-impact intelligence summary]. *(Source: [Source Name](URL))*

---

## 👔 CEO & FOUNDER WATCH
* **[Leader Name] ([Title, Organization/Company])**
  * **Statement/Action:** [Specific public action, statement, manifesto, or executive shift.]
  * **Classification:** 🔴 OFFICIAL ANNOUNCEMENT *(or 🟠 SIGNIFICANT STATEMENT)*
  * **Why It Matters:** [Strategic intent and impact on ecosystem.]
  * **Source:** [Source Name](URL)

(Include 2-3 prominent leaders)

---

## 🚀 STARTUP & FUNDING RADAR
* **[Company Name]:** [Funding round, valuation, investors, and product/market disruption details]. *(Source: [Source Name](URL))*
* **[Company Name]:** [Details]. *(Source: [Source Name](URL))*
* **[Sector Trend]:** [Details]. *(Source: [Source Name](URL))*

---

## 🧠 RESEARCH & BREAKTHROUGH RADAR
* **[Project/Model/Discovery Name] [[Prototype/Research/Commercial/Production]]:** [Breakthrough technical summary and real-world implications]. *(Source: [Source Name](URL))*
* **[Project/Model Name] [[Status]]:** [Details]. *(Source: [Source Name](URL))*

---

## 💻 DEVELOPER & SOFTWARE RADAR
* **[Tool/Framework/Language Update]:** [Developer ecosystem impact, architecture, or performance shift]. *(Source: [Source Name](URL))*
* **[Topic/Shift]:** [Details]. *(Source: [Source Name](URL))*

---

## ☁️ INFRASTRUCTURE RADAR
* **[Topic - e.g., Compute Securitization / HBM & Cooling / Optical Interconnects]:** [Data center, silicon supply, or cloud architecture insight]. *(Source: [Source Name](URL))*
* **[Topic]:** [Details]. *(Source: [Source Name](URL))*

---

## 🇮🇳 INDIA TECH WATCH
* **[Key Milestone/Initiative - e.g. Semicon 2.0 / IndiaAI / Digital Public Infrastructure]:** [Policy, investment, or technological milestone relevant to India's tech ecosystem]. *(Source: [Source Name](URL))*
* **[Global Alignment/Domestic Expansion]:** [Details]. *(Source: [Source Name](URL))*

---

## 📈 WHAT IS CHANGING IN TECH? (Emerging Patterns)
1. **[Pattern 1 Name]:** [Sharp synthesis of structural shift happening across the industry.]
2. **[Pattern 2 Name]:** [Sharp synthesis of structural shift happening across the industry.]
3. **[Pattern 3 Name]:** [Sharp synthesis of structural shift happening across the industry.]
4. **[Pattern 4 Name]:** [Sharp synthesis of structural shift happening across the industry.]

---

## 💡 ONE THING TO REMEMBER
"[A profound, memorable, 1-2 sentence executive quote summarizing the overarching strategic takeaway of today's tech shifts.]"

---
Raw News Articles to synthesize from:
{articles_block}
"""

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    resp = requests.post(
        endpoint,
        params={"key": GEMINI_API_KEY},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ---------------------------------------------------------------------------
# Step 3: Upload to Google Drive via Google Apps Script Webhook
# ---------------------------------------------------------------------------
def upload_to_drive(markdown_text: str) -> dict:
    today_str = datetime.date.today().strftime("%B %d, %Y")
    doc_title = f"TECH WORLD DAILY INTELLIGENCE - {today_str}"

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
    print(f"Fetched {len(articles)} unique articles.")

    print("Synthesizing 'TECH WORLD DAILY INTELLIGENCE' with Gemini...")
    briefing = summarize_with_gemini(articles)

    print("Uploading executive briefing to Google Drive...")
    result = upload_to_drive(briefing)

    print(f"Done! Created document -> {result.get('url', 'Uploaded')}")


if __name__ == "__main__":
    main()
