const https = require("https");

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";

const SOURCES = {
  reddit: [
    {
      name: "r/NevernessToEverness",
      rss: "https://www.reddit.com/r/NevernessToEverness/search.rss?q=guide+OR+tips+OR+how+OR+beginner+OR+tutorial+OR+best+OR+build+OR+team+OR+tier&sort=new&restrict_sr=1",
    },
    {
      name: "r/gachagaming — NTE guides",
      rss: "https://www.reddit.com/r/gachagaming/search.rss?q=neverness+to+everness+guide+OR+tips+OR+tier+OR+build&sort=new",
    },
  ],
};

const GUIDE_SIGNALS = [
  "guide","tips","how to","how i","tutorial","beginner","best","build","team",
  "tier","meta","rotation","farm","f2p","breakdown","explained","worth",
  "progression","resource","income","upgrade","skill","module","comp",
  "strategy","trick","optimize","setup","showcase",
];

const SKIP_SIGNALS = [
  "pulled","pity","lost 50/50","rant","complaint","vent","meme","fan art",
  "fanart","appreciation","daily","weekly","anyone else","missed","sad",
  "happy","got her","got him","finally","just got","i got",
];

function isGuidePost(title, summary) {
  const text = (title + " " + summary).toLowerCase();
  return GUIDE_SIGNALS.some((kw) => text.includes(kw)) &&
    !SKIP_SIGNALS.some((kw) => text.includes(kw));
}

function httpGet(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "NTEContentBot/1.0" } }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve(data));
    }).on("error", reject);
  });
}

function httpPost(url, body) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);
    const options = {
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
    };
    const req = https.request(url, options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve(data));
    });
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
}

async function fetchRedditPosts(rssUrl, fetchLimit = 25) {
  const posts = [];
  try {
    const raw = await httpGet(rssUrl);
    const entries = [...raw.matchAll(/<entry>([\s\S]*?)<\/entry>/g)];
    for (const [, entry] of entries.slice(0, fetchLimit)) {
      const get = (tag) => {
        const m = entry.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`));
        return m ? m[1].replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").trim() : "";
      };
      const linkMatch = entry.match(/<link[^>]+href="([^"]+)"/);
      const content = get("content")
        .replace(/<[^>]+>/g, " ")
        .replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&lt;/g, "").replace(/&gt;/g, "").replace(/&#\d+;/g, "")
        .replace(/\s+/g, " ").trim().slice(0, 600);
      posts.push({
        title: get("title") || "No title",
        link: linkMatch ? linkMatch[1] : "#",
        summary: content,
        published: get("updated"),
        author: get("name") || "Unknown",
      });
    }
  } catch (e) {
    console.error("Fetch error:", e.message);
  }
  return posts;
}

function fallbackPlan(post) {
  return {
    hook: `Here's everything you need to know: ${post.title.slice(0, 55)}`,
    content_type: "Guide",
    short_form: {
      platform: "TikTok / YouTube Shorts",
      duration: "30-45s",
      script_outline: [
        "Hook — tease the tip in one sentence",
        "Show the mechanic / tip on screen",
        "Explain why it matters",
        "CTA — follow for more NTE guides",
      ],
    },
    long_form: {
      platform: "YouTube",
      duration: "8-12 mins",
      title: `NTE Guide: ${post.title} — Full Breakdown`,
      sections: [
        "Intro — what we're covering and why",
        "Step-by-step walkthrough",
        "Common mistakes to avoid",
        "Best teams / builds to pair this with",
        "Outro + like & subscribe CTA",
      ],
    },
    thumbnail_texts: [
      "THIS GUIDE CHANGES EVERYTHING 🔥",
      "NTE PLAYERS NEED THIS",
      "BEST NTE GUIDE RIGHT NOW",
    ],
    hashtags: ["#NTE", "#NevernessToEverness", "#NTEguide", "#gachagaming", "#NTEcreator"],
    urgency: "medium",
    urgency_reason: "Solid evergreen guide — post anytime but sooner gets more early traction.",
  };
}

async function generateContentPlan(post) {
  if (!GEMINI_API_KEY) return fallbackPlan(post);

  const prompt = `You are a content strategist for a solo creator making YouTube and TikTok videos about "Neverness to Everness" (NTE), a popular urban open-world gacha RPG.

A guide or tips post has appeared. Use it to build a personal content plan for the creator.

POST TITLE: ${post.title}
POST SUMMARY: ${post.summary}

Return ONLY a valid JSON object — no markdown, no extra text:

{
  "hook": "One punchy attention-grabbing sentence for a short-form video (max 15 words, present tense)",
  "content_type": "One of: Guide, Tier List, Tips & Tricks, Showcase, Build Guide, Beginner Guide",
  "short_form": {
    "platform": "TikTok / YouTube Shorts",
    "duration": "15-45s",
    "script_outline": ["step 1", "step 2", "step 3", "step 4"]
  },
  "long_form": {
    "platform": "YouTube",
    "duration": "e.g. 8-12 mins",
    "title": "SEO-optimised YouTube title — specific, clickable, includes NTE",
    "sections": ["Intro", "section 2", "section 3", "section 4", "Outro + CTA"]
  },
  "thumbnail_texts": ["Option A (all caps, punchy)", "Option B", "Option C"],
  "hashtags": ["#NTE", "#NevernessToEverness", "#tag3", "#tag4", "#tag5"],
  "urgency": "high | medium | low",
  "urgency_reason": "One sentence — why post now or why it can wait"
}`;

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`;
    const raw = await httpPost(url, {
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.8, maxOutputTokens: 1024 },
    });
    const data = JSON.parse(raw);
    let text = data.candidates[0].content.parts[0].text.trim();
    text = text.replace(/^```[a-z]*\n?/, "").replace(/\n?```$/, "");
    return JSON.parse(text);
  } catch (e) {
    console.error("Gemini error:", e.message);
    return fallbackPlan(post);
  }
}

exports.handler = async (event) => {
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (event.httpMethod === "OPTIONS") return { statusCode: 200, headers, body: "" };

  try {
    const qs = event.queryStringParameters || {};
    const limit = parseInt(qs.limit || "6", 10);
    const platform = qs.platform || "reddit";
    const sources = SOURCES[platform] || SOURCES.reddit;

    const allPosts = [];
    for (const source of sources) {
      const raw = await fetchRedditPosts(source.rss, 25);
      const guides = raw.filter((p) => isGuidePost(p.title, p.summary));
      guides.forEach((p) => (p.source_name = source.name));
      allPosts.push(...guides);
    }

    const seen = new Set();
    const unique = allPosts.filter((p) => {
      if (seen.has(p.title)) return false;
      seen.add(p.title);
      return true;
    }).slice(0, limit);

    const results = await Promise.all(
      unique.map(async (post) => ({
        post,
        plan: await generateContentPlan(post),
        generated_at: new Date().toISOString(),
      }))
    );

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ success: true, count: results.length, filtered_to: "guides only", data: results }),
    };
  } catch (e) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ success: false, error: e.message, data: [] }),
    };
  }
};
