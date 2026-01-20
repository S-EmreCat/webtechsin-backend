# app/main.py
from pathlib import Path
import json

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .mailer import send_contact_email, ResendError
from .schemas import ContactIn

app = FastAPI(title="Webtechsin API")

# ✅ Hem Contact (POST) hem Services (GET) için CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prod'da daraltırsın
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -----------------------------
# Health
# -----------------------------
@app.get("/health")
def health():
    return {"ok": True}


# -----------------------------
# Services (JSON -> API)
# -----------------------------
DATA_PATH = Path(__file__).resolve().parent / "data" / "services.json"


def _load_services_catalog() -> dict:
    if not DATA_PATH.exists():
        return {"meta": {}, "services": []}
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@app.get("/services")
def get_services(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
):
    """
    Flutter catalog format:
    {
      "meta": {...},
      "services": [...]
    }

    Query:
    - category: 'Web' / 'Video' / 'Dijital Pazarlama' (veya 'Tümü')
    - q: title/description search
    - featured=true: sadece featuredServiceIds içindekiler
    """
    catalog = _load_services_catalog()
    services = catalog.get("services", []) or []
    meta = catalog.get("meta", {}) or {}

    if category and category.lower() != "tümü":
        services = [s for s in services if s.get("category") == category]

    if q:
        ql = q.strip().lower()
        services = [
            s
            for s in services
            if ql in (s.get("title", "").lower())
            or ql in (s.get("description", "").lower())
        ]

    if featured is True:
        featured_ids = meta.get("featuredServiceIds") or []
        services = [s for s in services if s.get("id") in featured_ids]

    return JSONResponse({"meta": meta, "services": services})


# -----------------------------
# Contact
# -----------------------------
@app.post("/contact", status_code=202)
async def contact(payload: ContactIn, x_api_key: str | None = Header(default=None)):
    if x_api_key != settings.contact_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if payload.honeypot.strip():
        raise HTTPException(status_code=400, detail="Invalid submission")

    try:
        await send_contact_email(
            name=payload.name,
            email=str(payload.email),
            message=payload.message,
        )
    except ResendError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"ok": True}
