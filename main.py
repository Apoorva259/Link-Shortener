import os
import sqlite3
import string
import random
from datetime import datetime
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

DB_PATH = os.environ.get("DB_PATH", "shortener.db")
CODE_LENGTH = 6
ALPHABET = string.ascii_letters + string.digits

app = FastAPI(title="URL Shortener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                code TEXT PRIMARY KEY,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0
            )
            """
        )


init_db()


class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_code: str | None = None


class ShortenResponse(BaseModel):
    code: str
    original_url: str
    short_url: str


def generate_code(length: int = CODE_LENGTH) -> str:
    return "".join(random.choices(ALPHABET, k=length))


def code_exists(conn, code: str) -> bool:
    row = conn.execute("SELECT 1 FROM urls WHERE code = ?", (code,)).fetchone()
    return row is not None


@app.post("/api/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, request: Request):
    with get_db() as conn:
        if payload.custom_code:
            code = payload.custom_code.strip()
            if not code.isalnum():
                raise HTTPException(400, "Custom code must be alphanumeric")
            if code_exists(conn, code):
                raise HTTPException(409, "That custom code is already taken")
        else:
            code = generate_code()
            # extremely unlikely collision loop, but handle it anyway
            while code_exists(conn, code):
                code = generate_code()

        conn.execute(
            "INSERT INTO urls (code, original_url, created_at, clicks) VALUES (?, ?, ?, 0)",
            (code, str(payload.url), datetime.utcnow().isoformat()),
        )

    base_url = str(request.base_url).rstrip("/")
    return ShortenResponse(
        code=code,
        original_url=str(payload.url),
        short_url=f"{base_url}/{code}",
    )


@app.get("/api/stats/{code}")
def get_stats(code: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM urls WHERE code = ?", (code,)).fetchone()
        if not row:
            raise HTTPException(404, "Short code not found")
        return {
            "code": row["code"],
            "original_url": row["original_url"],
            "created_at": row["created_at"],
            "clicks": row["clicks"],
        }


@app.get("/api/urls")
def list_urls():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM urls ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
        return [
            {
                "code": r["code"],
                "original_url": r["original_url"],
                "created_at": r["created_at"],
                "clicks": r["clicks"],
            }
            for r in rows
        ]


@app.get("/{code}")
def redirect_to_url(code: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM urls WHERE code = ?", (code,)).fetchone()
        if not row:
            raise HTTPException(404, "Short link not found")
        conn.execute("UPDATE urls SET clicks = clicks + 1 WHERE code = ?", (code,))
    return RedirectResponse(row["original_url"])


# Serve the frontend last so it doesn't shadow the API/redirect routes above.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
