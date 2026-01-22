import httpx
from .config import settings

RESEND_SEND_URL = "https://api.resend.com/emails"


class ResendError(Exception):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"Resend error {status_code}: {body}")
        self.status_code = status_code
        self.body = body


async def send_contact_email(*, name: str, email: str, message: str) -> None:
    subject = f"[Contact] {name} <{email}>"
    text = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}\n"

    payload = {
        "from": settings.contact_from,
        "to": [settings.contact_to],
        "subject": subject,
        "text": text,
        "reply_to": email,
    }

    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(RESEND_SEND_URL, json=payload, headers=headers)
        if r.status_code >= 400:
            raise ResendError(r.status_code, r.text)
