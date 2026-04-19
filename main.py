"""
Kenya Tax Q&A — FastAPI + Groq Free API demo.

Streams answers token-by-token over Server-Sent Events. Uses Groq's
free tier (no API costs). Fast inference with Llama 3.1 70B.

Run locally:
    pip install -r requirements.txt
    export GROQ_API_KEY=gsk_...
    uvicorn main:app --reload

Deploy to Railway: set GROQ_API_KEY in the service env, push, done.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import AsyncIterator

from groq import AsyncGroq
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from system_prompt import KENYA_TAX_SYSTEM_PROMPT

MODEL = "llama-3.1-70b-versatile"
MAX_TOKENS = 2048
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Kenya Tax Q&A",
    description="Ask any question about Kenyan tax law. Powered by Groq (free).",
    version="1.0.0",
)

client = AsyncGroq()  # reads GROQ_API_KEY from env


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
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(500, "GROQ_API_KEY not configured on server")

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            async with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=KENYA_TAX_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": req.question}],
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield _sse("token", {"text": text})

                final = await stream.get_final_message()
                usage = final.usage if hasattr(final, "usage") else None
                input_tokens = usage.input_tokens if usage else 0
                output_tokens = usage.output_tokens if usage else 0
                
                yield _sse(
                    "done",
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cache_read": 0,
                        "cache_write": 0,
                    },
                )
        except Exception as e:  # noqa: BLE001
            import traceback
            error_msg = f"{str(e)[:200]}\n{traceback.format_exc()[:100]}"
            yield _sse("error", {"message": error_msg})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
