import base64
import hashlib
import hmac
import json
import logging
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware


from src.db.models import (
    User,
    ChatSession,
    ChatMessage,
    Book,
    BookChunk,
)

from src.admin.views import (
    UserAdmin,
    ChatSessionAdmin,
    ChatMessageAdmin,
    BookAdmin,
    BookChunkAdmin,
    AdminUserAdmin,
)

from src.admin.auth import AdminAuth
from src.db.postgres import sync_engine

logging.basicConfig(level=logging.INFO)

SECRET_KEY = "my_super_secret_key_123"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="admin_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=False,
)

# src/templates papkasiga to'g'ri yo'l ko'rsatish
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


class TokenSchema(BaseModel):
    token: str


def verify_token(token: str):
    if "." not in token:
        raise HTTPException(
            status_code=400, detail="Token formati noto'g'ri (nuqta yo'q)!"
        )

    parts = token.split(".")
    if len(parts) != 2:
        raise HTTPException(
            status_code=400, detail="Token strukturasi noto'g'ri!"
        )

    encoded_data, signature = parts[0], parts[1]

    # Base64URL padding to'g'rilash
    padding = "=" * ((4 - len(encoded_data) % 4) % 4)
    padded_data = encoded_data + padding

    try:
        decoded_bytes = base64.urlsafe_b64decode(padded_data)
        json_payload = decoded_bytes.decode("utf-8")
        payload = json.loads(json_payload)
    except Exception as e:
        logging.error(f"Base64 dekodlash xatosi: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Base64 dekodlash xatosi: {str(e)}"
        )

    # Imzoni tekshirish
    expected_signature = hmac.new(
        SECRET_KEY.encode(), encoded_data.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        logging.error(
            f"Imzo mos kelmadi! Kelgan: {signature}, Kutilgan: {expected_signature}"
        )
        raise HTTPException(
            status_code=401, detail="Noto'g'ri token imzosi!"
        )

    return payload


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )


@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request):
    return templates.TemplateResponse(
        "quiz.html",
        {"request": request}
    )


@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap_page(request: Request):
    return templates.TemplateResponse(
        "roadmap.html",
        {"request": request}
    )

@app.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    return templates.TemplateResponse(
        "statistics.html",
        {"request": request}
    )


@app.post("/api/verify-token")
async def api_verify_token(data: TokenSchema):
    if not data.token:
        raise HTTPException(status_code=400, detail="Token topilmadi!")

    user_data = verify_token(data.token)
    return {"status": "success", "user": user_data}


authentication_backend = AdminAuth(
    secret_key=SECRET_KEY,
)

admin = Admin(
    app,
    sync_engine,
    authentication_backend=authentication_backend,
)

admin.add_view(UserAdmin)
admin.add_view(ChatSessionAdmin)
admin.add_view(ChatMessageAdmin)
admin.add_view(BookAdmin)
admin.add_view(BookChunkAdmin)
admin.add_view(AdminUserAdmin)