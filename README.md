# Kenya Tax Q&A 🇰🇪

A free, instant Q&A assistant for Kenyan tax law — PAYE, VAT, TOT, WHT,
NSSF, SHIF, Housing Levy, TCC, iTax deadlines — powered by Claude
(`claude-opus-4-7`).

Live demo: **https://cheerful-reflection-production.up.railway.app/**

## Why this exists

Kenyan taxpayers pay for basic answers that a language model can give
for free in seconds. This is a minimal, production-shaped reference
showing how to wire Claude's Messages API with streaming and prompt
caching for a Kenya-specific knowledge base.

## Architecture

```
Browser ──POST /ask──► FastAPI ──messages.stream──► Anthropic API
   ▲                     │                            │
   │   SSE token stream  │   prompt-cached system     │
   └─────────────────────┘   prompt (~5K tokens)      │
                             cached at 0.1× rate ─────┘
```

- **Model**: `claude-opus-4-7` with adaptive thinking
- **Streaming**: Server-Sent Events; the frontend renders tokens as they arrive
- **Prompt caching**: the Kenya tax knowledge base is attached once with
  `cache_control: {"type": "ephemeral"}`. Every request after the first
  reads it at ~10% of input cost
- **Stateless**: no database, no auth — sessions live only in the browser

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — `/ask` SSE streaming endpoint, `/` serves the UI |
| `system_prompt.py` | Kenya tax law system prompt (2025/26 Finance Act figures) |
| `static/index.html` | Vanilla-JS single-file chat UI consuming the SSE stream |
| `requirements.txt` | `anthropic`, `fastapi`, `uvicorn`, `pydantic` |
| `Procfile` / `railway.json` | Railway deployment config |
| `.env.example` | Expected env: `ANTHROPIC_API_KEY` |

## Run locally

```bash
git clone https://github.com/steph851/kenya-tax-qa
cd kenya-tax-qa
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload
```

Open http://localhost:8000.

## Deploy to Railway

1. Push this repo to GitHub.
2. On [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → pick this repo.
3. Under the service → **Variables**, set `ANTHROPIC_API_KEY` (get one at [console.anthropic.com](https://console.anthropic.com)).
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
