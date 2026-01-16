from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .mailer import send_contact_email, ResendError

from .schemas import ContactIn
from .config import settings
from .mailer import send_contact_email

app = FastAPI(title="Webtechsin Contact API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prod'da daraltırsın
    allow_methods=["POST"],
    allow_headers=["*"],
)

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
        # Resend politikası / dış servis hatası -> 502 mantıklı
        raise HTTPException(status_code=502, detail=str(e))

    return {"ok": True}

    return {"ok": True}
