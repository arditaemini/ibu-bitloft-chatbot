"""Web server for the IBU BITLoft chatbot.

Run:  python app.py      then open http://localhost:8000

Created by the BITLoft Team, International Balkan University.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag import Chatbot

STATIC_DIR = Path(__file__).resolve().parent / "static"
bot = None
startup_error = None


@asynccontextmanager
async def lifespan(_app):
    global bot, startup_error
    try:
        bot = Chatbot()
    except Exception as exc:  # keep serving the page so the error is visible
        startup_error = str(exc)
        print(f"Chatbot failed to start: {exc}")
    yield


app = FastAPI(title="IBU BITLoft Chatbot", lifespan=lifespan)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: List[Message] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


@app.get("/api/health")
def health():
    return {"ready": bot is not None, "error": startup_error}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if bot is None:
        raise HTTPException(503, startup_error or "The chatbot is still starting.")
    try:
        return await run_in_threadpool(
            bot.ask, req.message, [m.model_dump() for m in req.history]
        )
    except Exception as exc:
        print(f"Error answering question: {exc}")
        raise HTTPException(502, "The language model could not answer right now. Please try again.")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )
