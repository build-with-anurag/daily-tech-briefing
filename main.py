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
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
DRIVE_WEBHOOK_URL = os.environ["DRIVE_WEBHOOK_URL"]

# Use a valid Gemini model ID for the Google Generative Language API.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ---------------------------------------------------------------------------
# Step 1: Fetch comprehensive news across global tech & India ecosystem
# ---------------------------------------------------------------------------
def fetch_news() -> list[dict]:
    articles = []

    # 1. Global top technology headlines
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"category": "technology", "language": "en", "pageSize": 30, "apiKey": NEWS_API_KEY}
        resp = requests.get(url, params=params, timeout=30)
        if resp.ok:
            articles.extend(resp.json().get("articles", []))
    except Exception as e:
        print("Warning fetching top headlines:", e)

    # 1.5. India-centric tech headlines
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"country": "in", "category": "technology", "pageSize": 30, "apiKey": NEWS_API_KEY}
        resp = requests.get(url, params=params, timeout=30)
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
            "apiKey": NEWS_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=30)
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

    prompt = f"""You are the Chief Intelligence Officer and lead author of "TECH WORLD DAILY INTELLIGENCE" — the premier strategic briefing read by C-suite executives, tier-1 venture capitalist[...]

Date of Briefing: {today_str}

Author today's comprehensive intelligence report based on the provided raw news stream. Emulate the exact structure, rigorous analytical depth, institutional tone, and strategic precision shown i[...]

CRITICAL INSTRUCTION: Strongly prioritize and prominently feature India-centric technology news, startups, policies, and developments throughout the report (especially in the TOP 5 DEVELOPMENTS).[...]

### MANDATORY REFERENCE STRUCTURE & STYLE GUIDELINE:

🌐 TECH WORLD DAILY INTELLIGENCE
Date: {today_str}
Topic: [3-4 major narrative anchors of today, e.g. "NVIDIA $105B OpenAI Ohio Campus, QpiAI Quantum Foundry & IndiaAI GPU Scale"]
Overall Tech Pulse: [A dense, highly strategic 2-3 sentence paragraph capturing the overarching macro shift, capital allocation, technology transition, and geopolitical/industry posture.]

🔥 TOP 5 DEVELOPMENTS

1. [Bold, Concrete Headline with Exact Financial Numbers / Key Metric / Action]
● Importance: [Score, e.g. 10/10 (Industry Defining) or 9/10 (High Impact) or 8/10 (High Impact)]
● Category: [Specific strategic category, e.g. Infrastructure & Big Tech Finance / Artificial Intelligence & Open Source / Sovereign Semiconductors & India Tech / AI Cybersecurity & Defense / Data Center Capital & Supply Chains]
● Verification Status: 🔴 Confirmed ([Official Release / Securities Filings / Ministry Gazette & PIB Disclosures / Company Announcement & Facility Launch / Industry Summit])
● What Happened: [Deep, rigorous 3-4 sentence breakdown with precise names, entities, numbers, specs, and strategic actions.]
● Why It Matters: [Deep macroeconomic, competitive moat, capital expenditure, and industry structural analysis.]
● What Changed: [Direct, incisive paradigm shift comparison: "Previously... Now..."]
● What's Next: [Concrete forward-looking timeline, roadmap milestones, regulatory actions, or hardware delivery dates.]
● Source: [Source Name](URL)
● Independent Coverage: [Secondary Source Name](URL) [if available from raw list, else omit]

(Provide all 5 developments with identical depth, structure, and bullet points)

🤖 AI RADAR
1. [Headline/Theme]: [1-2 sentence dense intelligence summary on model architectures, post-training, or benchmarks]. (Source: [Source Name](URL))
2. [Headline/Theme]: [1-2 sentence dense intelligence summary]. (Source: [Source Name](URL))
3. [Headline/Theme]: [1-2 sentence dense intelligence summary]. (Source: [Source Name](URL))
4. [Headline/Theme]: [1-2 sentence dense intelligence summary]. (Source: [Source Name](URL))

👔 CEO & FOUNDER WATCH
● [Leader Full Name] ([Title, Company/Organization])
  ○ Statement/Action: [Specific executive directive, public manifesto, restructuring, or strategic quote.]
  ○ Classification: 🔴 OFFICIAL ANNOUNCEMENT (or 🟠 SIGNIFICANT STATEMENT)
  ○ Why It Matters: [Strategic implications on market dominance and enterprise mindshare.]
  ○ Source: [Source Name](URL)
(Include 2-3 prominent executives/ministers, e.g. Jensen Huang, Sam Altman, Mark Zuckerberg, Dario Amodei, Ashwini Vaishnaw, etc.)

🚀 STARTUP & FUNDING RADAR
● [Company Name]: [Funding round, valuation, tier-1 investors, and disruptive technology angle]. (Source: [Source Name](URL))
● [Company Name]: [Details]. (Source: [Source Name](URL))
● [Sector Capital Flow]: [Details]. (Source: [Source Name](URL))

🧠 RESEARCH & BREAKTHROUGH RADAR
● [Project / Model Name] [[Prototype/Research/Commercial/Production]]: [Breakthrough technical summary, parameter counts, benchmarks, or efficiency improvements]. (Source: [Source Name](URL))
● [Project Name] [[Status]]: [Details]. (Source: [Source Name](URL))
● [Project Name] [[Status]]: [Details]. (Source: [Source Name](URL))

💻 DEVELOPER & SOFTWARE RADAR
● [Tool / Framework / Agent Runtime / Workflow Shift]: [Technical developer ecosystem impact, runtime specs, or workflow transition]. (Source: [Source Name](URL))
● [Topic]: [Details]. (Source: [Source Name](URL))

☁️ INFRASTRUCTURE RADAR
● [Compute Securitization / Liquid Cooling / Silicon Photonics / Power Substations]: [Data center energy, high-bandwidth memory (HBM), optical interconnects, or wafer-scale cluster insight]. (Source: [Source Name](URL))
● [Topic]: [Details]. (Source: [Source Name](URL))

🇮🇳 INDIA TECH WATCH
● [Semicon 2.0 / IndiaAI / Fab Construction / Domestic DeepTech]: [Specific progress on India's semiconductor manufacturing, sovereign compute grid, or deeptech funding]. (Source: [Source Name](URL))
● [Initiative Name]: [Details]. (Source: [Source Name](URL))

📈 WHAT IS CHANGING IN TECH? (Emerging Patterns)
1. [Pattern 1 Name]: [Sharp, authoritative synthesis of structural transition happening across global tech.]
2. [Pattern 2 Name]: [Sharp synthesis of structural transition.]
3. [Pattern 3 Name]: [Sharp synthesis of structural transition.]
4. [Pattern 4 Name]: [Sharp synthesis of structural transition.]

💡 ONE THING TO REMEMBER
"[A profound, memorable, 1-2 sentence executive quote capturing the overarching macro insight of today's tech developments.]"

---
Raw News Stream:
{articles_block}
"""

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    max_retries = 4
    delay = 5

    for attempt in range(max_retries + 1):
        resp = requests.post(
            endpoint,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.25},
            },
            timeout=150,
        )

        if resp.status_code in (429, 500, 503):
            if attempt < max_retries:
                print(f"Server busy (status {resp.status_code}), retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
                continue

        if not resp.ok:
            try:
                error_details = resp.json()
            except ValueError:
                error_details = resp.text
            raise RuntimeError(
                f"Gemini API request failed with HTTP {resp.status_code}: {error_details}"
            )

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Gemini response: {data}") from exc


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
        return f"{today_iso} [Tech] — {topic}"

    return f"{today_iso} [Tech] — Daily Intelligence Briefing"


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
