import json
import urllib.request
import urllib.parse
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SOURCES = {
    "reddit": [
        {
            "name": "r/NevernessToEverness",
            "rss": "https://www.reddit.com/r/NevernessToEverness/search.rss?q=guide+OR+tips+OR+how+OR+beginner+OR+tutorial+OR+best+OR+build+OR+team+OR+tier&sort=new&restrict_sr=1",
        },
        {
            "name": "r/gachagaming — NTE guides",
            "rss": "https://www.reddit.com/r/gachagaming/search.rss?q=neverness+to+everness+guide+OR+tips+OR+tier+OR+build&sort=new",
        },
    ]
}

GUIDE_SIGNALS = [
    "guide", "tips", "how to", "how i", "tutorial", "beginner",
    "best", "build", "team", "tier", "meta", "rotation", "farm",
    "f2p", "breakdown", "explained", "worth", "progression",
    "resource", "income", "upgrade", "skill", "module", "comp",
    "strategy", "trick", "optimize", "setup", "showcase",
]

SKIP_SIGNALS = [
    "pulled", "pity", "lost 50/50", "rant", "complaint", "vent",
    "meme", "fan art", "fanart", "appreciation", "daily", "weekly",
    "anyone else", "missed", "sad", "happy", "got her", "got him",
    "finally", "just got", "i got",
]

def is_guide_post(title, summary):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in GUIDE_SIGNALS) and not any(kw in text for kw in SKIP_SIGNALS)

def fetch_reddit_posts(rss_url, fetch_limit=25):
    posts = []
    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "NTEContentBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns)[:fetch_limit]:
            title   = (entry.find("atom:title",   ns) or type('', (), {'text': 'No title'})()).text or "No title"
            link_el =  entry.find("atom:link",    ns)
            content = (entry.find("atom:content", ns) or type('', (), {'text': ''})()).text or ""
            updated = (entry.find("atom:updated", ns) or type('', (), {'text': ''})()).text or ""
            author  = (entry.find("atom:author/atom:name", ns) or type('', (), {'text': 'Unknown'})()).text or "Unknown"
            link = link_el.get("href") if link_el is not None else "#"
            clean = re.sub(r'<[^>]+>', ' ', content)
            clean = re.sub(r'\s+', ' ', clean).strip()[:600]
            posts.append({"title": title, "link": link, "summary": clean, "published": updated, "author": author})
    except Exception as e:
        print(f"Fetch error: {e}")
    return posts

def generate_content_plan(post):
    if not GEMINI_API_KEY:
        return _fallback_plan(post)
    prompt = f"""You are a content strategist for a solo creator making YouTube and TikTok videos about "Neverness to Everness" (NTE), a popular urban open-world gacha RPG.

A guide or tips post has appeared. Use it to build a personal content plan for the creator.

POST TITLE: {post['title']}
POST SUMMARY: {post['summary']}

Return ONLY a valid JSON object — no markdown, no extra text:

{{
  "hook": "One punchy attention-grabbing sentence for a short-form video (max 15 words, present tense)",
  "content_type": "One of: Guide, Tier List, Tips & Tricks, Showcase, Build Guide, Beginner Guide",
  "short_form": {{
    "platform": "TikTok / YouTube Shorts",
    "duration": "15-45s",
    "script_outline": ["step 1", "step 2", "step 3", "step 4"]
  }},
  "long_form": {{
    "platform": "YouTube",
    "duration": "e.g. 8-12 mins",
    "title": "SEO-optimised YouTube title — specific, clickable, includes NTE",
    "sections": ["Intro", "section 2", "section 3", "section 4", "Outro + CTA"]
  }},
  "thumbnail_texts": ["Option A (all caps, punchy)", "Option B", "Option C"],
  "hashtags": ["#NTE", "#NevernessToEverness", "#tag3", "#tag4", "#tag5"],
  "urgency": "high | medium | low",
  "urgency_reason": "One sentence — why post now or why it can wait"
}}"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1024}
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r'^```[a-z]*\n?', '', raw.strip())
        raw = re.sub(r'\n?```$', '', raw.strip())
        return json.loads(raw)
    except Exception as e:
        print(f"Gemini error: {e}")
        return _fallback_plan(post)

def _fallback_plan(post):
    return {
        "hook": f"Here's everything you need to know: {post['title'][:55]}",
        "content_type": "Guide",
        "short_form": {
            "platform": "TikTok / YouTube Shorts",
            "duration": "30-45s",
            "script_outline": [
                "Hook — tease the tip in one sentence",
                "Show the mechanic / tip on screen",
                "Explain why it matters",
                "CTA — follow for more NTE guides"
            ]
        },
        "long_form": {
            "platform": "YouTube",
            "duration": "8-12 mins",
            "title": f"NTE Guide: {post['title']} — Full Breakdown",
            "sections": [
                "Intro — what we're covering and why",
                "Step-by-step walkthrough",
                "Common mistakes to avoid",
                "Best teams / builds to pair this with",
                "Outro + like & subscribe CTA"
            ]
        },
        "thumbnail_texts": [
            "THIS GUIDE CHANGES EVERYTHING 🔥",
            "NTE PLAYERS NEED THIS",
            "BEST NTE GUIDE RIGHT NOW"
        ],
        "hashtags": ["#NTE", "#NevernessToEverness", "#NTEguide", "#gachagaming", "#NTEcreator"],
        "urgency": "medium",
        "urgency_reason": "Solid evergreen guide — post anytime but sooner gets more early traction."
    }


def handler(event, context):
    """Netlify serverless function handler."""
    # CORS headers for all responses
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    # Handle preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        qs = event.get("queryStringParameters") or {}
        limit    = int(qs.get("limit", "6"))
        platform = qs.get("platform", "reddit")

        sources = SOURCES.get(platform, SOURCES["reddit"])

        all_posts = []
        for source in sources:
            raw    = fetch_reddit_posts(source["rss"], fetch_limit=25)
            guides = [p for p in raw if is_guide_post(p["title"], p["summary"])]
            for p in guides:
                p["source_name"] = source["name"]
            all_posts.extend(guides)

        # Deduplicate by title
        seen, unique = set(), []
        for p in all_posts:
            if p["title"] not in seen:
                seen.add(p["title"])
                unique.append(p)
        unique = unique[:limit]

        results = []
        for post in unique:
            plan = generate_content_plan(post)
            results.append({
                "post": post,
                "plan": plan,
                "generated_at": datetime.now(timezone.utc).isoformat()
            })

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "success": True,
                "count": len(results),
                "filtered_to": "guides only",
                "data": results
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"success": False, "error": str(e), "data": []})
        }