from pydantic import BaseModel, EmailStr, Field


class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    message: str = Field(min_length=5, max_length=2000)
    honeypot: str = ""  # UI'da görünmeyen alan, hep boş kalmalı
