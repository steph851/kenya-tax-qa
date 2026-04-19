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

from groq import Groq
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

client = Groq()  # reads GROQ_API_KEY from env


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
            # Call Groq API for streaming chat
            messages = [
                {"role": "system", "content": KENYA_TAX_SYSTEM_PROMPT},
                {"role": "user", "content": req.question},
            ]
            
            # Try different ways to call Groq API
            try:
                # Try OpenAI-compatible syntax
                stream = client.chat.completions.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    stream=True,
                )
            except AttributeError:
                # Fallback if chat.completions doesn't exist
                stream = client.completions.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    prompt=f"System: {KENYA_TAX_SYSTEM_PROMPT}\n\nUser: {req.question}",
                    stream=True,
                )
            
            total_input_tokens = 0
            total_output_tokens = 0
            
            for chunk in stream:
                # Handle both OpenAI-style and other response formats
                if hasattr(chunk, "choices") and chunk.choices:
                    if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                        content = chunk.choices[0].delta.content
                        if content:
                            yield _sse("token", {"text": content})
                    elif hasattr(chunk.choices[0], "text"):
                        # Handle text_completion style responses
                        if chunk.choices[0].text:
                            yield _sse("token", {"text": chunk.choices[0].text})
                
                # Track token usage
                if hasattr(chunk, "usage") and chunk.usage:
                    if hasattr(chunk.usage, "prompt_tokens"):
                        total_input_tokens = chunk.usage.prompt_tokens or 0
                    if hasattr(chunk.usage, "completion_tokens"):
                        total_output_tokens = chunk.usage.completion_tokens or 0
            
            yield _sse(
                "done",
                {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cache_read": 0,
                    "cache_write": 0,
                },
            )
        except Exception as e:  # noqa: BLE001
            error_str = str(e)
            yield _sse("error", {"message": f"Groq API Error: {error_str[:250]}"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
