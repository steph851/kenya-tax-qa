"""
Kenya Tax Q&A — FastAPI + Anthropic Claude API demo.

Streams answers token-by-token over Server-Sent Events. The Kenya tax
system prompt is large (~4K+ tokens) and cached with ephemeral
cache_control so every request after the first reads it at 0.1× input
cost.

Run locally:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    uvicorn main:app --reload

Deploy to Railway: set ANTHROPIC_API_KEY in the service env, push, done.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import AsyncIterator

from anthropic import AsyncAnthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from system_prompt import KENYA_TAX_SYSTEM_PROMPT

MODEL = "claude-opus-4-7"
MAX_TOKENS = 2048
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Kenya Tax Q&A",
    description="Ask any question about Kenyan tax law. Powered by Claude.",
    version="1.0.0",
)

client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}


@app.post("/ask")
async def ask(req: AskRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured on server")

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            async with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": KENYA_TAX_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": req.question}],
                thinking={"type": "adaptive"},
            ) as stream:
                async for text in stream.text_stream:
                    yield _sse("token", {"text": text})

                final = await stream.get_final_message()
                yield _sse(
                    "done",
                    {
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens,
                        "cache_read": getattr(final.usage, "cache_read_input_tokens", 0),
                        "cache_write": getattr(final.usage, "cache_creation_input_tokens", 0),
                    },
                )
        except Exception as e:  # noqa: BLE001
            yield _sse("error", {"message": str(e)[:300]})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
