from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import ContactIn
from .mailer import ResendError, send_contact_email

app = FastAPI(title="Webtechsin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent / "data"
SERVICES_FILE = DATA_DIR / "services.json"


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/services")
def get_services():
    try:
        raw = SERVICES_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="services.json not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contact", status_code=202)
async def contact(payload: ContactIn, x_api_key: str | None = Header(default=None)):
    if x_api_key != settings.contact_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # bot/abuse yakalama (UI'da görünmez alan)
    if payload.honeypot.strip():
        raise HTTPException(status_code=400, detail="Invalid submission")

    try:
        await send_contact_email(
            name=payload.name,
            email=str(payload.email),
            message=payload.message,
        )
    except ResendError as e:
        # upstream mail provider hatası
        raise HTTPException(status_code=502, detail=str(e))

    return {"ok": True}
