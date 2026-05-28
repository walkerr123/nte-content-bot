# NTE Studio — Backend (Netlify)

Fetches NTE guide posts from Reddit, filters out pulls/memes/rants,
and generates step-by-step content plans via Google Gemini (free tier).

## Project structure

```
nte-studio/
├── netlify/
│   └── functions/
│       ├── content.py   ← main endpoint
│       └── health.py    ← health check
├── public/
│   └── index.html       ← replace with your frontend build
├── netlify.toml
├── requirements.txt
└── .gitignore
```

## API endpoints

Once deployed your frontend calls these clean URLs:

| Endpoint | Description |
|---|---|
| `GET /api/content?limit=6&platform=reddit` | Guide posts + AI content plans |
| `GET /api/health` | Status + config check |

Raw Netlify function URLs also work:
- `/.netlify/functions/content`
- `/.netlify/functions/health`

## Deploy steps

### 1. Get a free Gemini API key
1. Go to https://aistudio.google.com/apikey
2. Sign in with Google → Create API key
3. Copy it

### 2. Push to GitHub
```bash
git init
git add .
git commit -m "NTE Studio backend"
git remote add origin https://github.com/YOUR_USERNAME/nte-studio.git
git push -u origin main
```

### 3. Deploy on Netlify
1. Go to https://netlify.com → Log in
2. Click **Add new site** → **Import an existing project** → GitHub
3. Select your repo
4. Build settings (auto-detected from netlify.toml):
   - Build command: *(leave blank)*
   - Publish directory: `public`
5. Click **Show advanced** → **New variable**:
   - Key: `GEMINI_API_KEY`
   - Value: your key from step 1
6. Click **Deploy site**

### 4. Test it
```
https://your-site.netlify.app/api/health
https://your-site.netlify.app/api/content?limit=3
```

## Frontend integration

Your frontend calls the API like this:

```js
const res = await fetch('https://your-site.netlify.app/api/content?limit=6&platform=reddit');
const { data } = await res.json();
// data = array of { post, plan, generated_at }
```

Each card maps to one item. The `plan` object contains:
- `hook` — short-form video hook line
- `content_type` — Guide / Tier List / Tips & Tricks / etc.
- `short_form` — platform, duration, 4-step script outline
- `long_form` — YouTube title, duration, 5 sections
- `thumbnail_texts` — 3 thumbnail copy options
- `hashtags` — 5 hashtags
- `urgency` — high / medium / low
- `urgency_reason` — one sentence

## Notes
- Zero external Python packages — pure stdlib
- Gemini `gemini-1.5-flash` free tier: 1500 requests/day
- Falls back to a smart static plan if Gemini fails
- Guide filter runs before Gemini to avoid wasting API calls on junk posts