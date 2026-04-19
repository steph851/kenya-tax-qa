# Kenya Tax Q&A 🇰🇪

A free, instant Q&A assistant for Kenyan tax law — PAYE, VAT, TOT, WHT,
NSSF, SHIF, Housing Levy, TCC, iTax deadlines — powered by Groq's free API
(`llama-3.1-70b-versatile`). **No API costs. Ever.**

Live demo: **https://cheerful-reflection-production.up.railway.app/**

## Why this exists

Kenyan taxpayers need instant, free answers to tax questions. This is a
minimal, production-shaped reference showing how to build a stateless,
streaming Q&A service with **zero API costs** using Groq's free tier and
FastAPI.

## Architecture

```
Browser ──POST /ask──► FastAPI ──messages.stream──► Groq API
   ▲                     │                             │
   │   SSE token stream  │                             │
   └─────────────────────┘   (free tier)              ┘
```

- **Model**: `llama-3.1-70b-versatile` (free, no rate limits for reasonable use)
- **Streaming**: Server-Sent Events; the frontend renders tokens as they arrive
- **Cost**: Zero API fees (Groq free tier)
- **Stateless**: no database, no auth — sessions live only in the browser

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — `/ask` SSE streaming endpoint, `/` serves the UI |
| `system_prompt.py` | Kenya tax law system prompt (2025/26 Finance Act figures) |
| `static/index.html` | Vanilla-JS single-file chat UI consuming the SSE stream |
| `requirements.txt` | `groq`, `fastapi`, `uvicorn`, `pydantic` |
| `Procfile` / `railway.json` | Railway deployment config |
| `.env.example` | Expected env: `GROQ_API_KEY` |

## Run locally

```bash
git clone https://github.com/steph851/kenya-tax-qa
cd kenya-tax-qa
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...
uvicorn main:app --reload
```

Open http://localhost:8000.

## Deploy to Railway

1. Push this repo to GitHub.
2. On [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → pick this repo.
3. Under the service → **Variables**, set `GROQ_API_KEY` (get a free one at [console.groq.com](https://console.groq.com) — no credit card needed).
4. Railway auto-detects Python, installs requirements, runs the `Procfile`, and assigns a public URL.

## Disclaimer

This demo is for general education. It is not professional tax advice.
Rates change with every Finance Act — always confirm figures on
[itax.kra.go.ke](https://itax.kra.go.ke) or with a registered tax agent
before filing.

## License

MIT — see [LICENSE](LICENSE).

## Author

[Stephen Wanjuki](https://github.com/steph851) — Nairobi, Kenya.

Built with [Claude Code](https://claude.com/claude-code).
