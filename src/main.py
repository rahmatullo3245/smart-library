import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from src.admin.auth import AdminAuth
from src.admin.views import (
    UserAdmin,
    ChatSessionAdmin,
    ChatMessageAdmin,
    BookAdmin,
    BookChunkAdmin,
    AdminUserAdmin,
)

from src.api.auth import (
    router as auth_router,
    api_router as auth_api_router,
)

from src.db.models import (
    User,
    ChatSession,
    ChatMessage,
    Book,
    BookChunk,
)

from src.db.postgres import sync_engine
from src.api.chat import router as chat_router

logging.basicConfig(level=logging.INFO)

# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

SECRET_KEY = "my_super_secret_key_123"

app = FastAPI()

# --------------------------------------------------
# API routers
# --------------------------------------------------

# SSO autentifikatsiyasi: /auth/...
app.include_router(auth_router)

# Token tekshirish va PostgreSQL foydalanuvchi sinxronlash:
# POST /api/verify-token
app.include_router(auth_api_router)

app.include_router(chat_router)

# --------------------------------------------------
# CORS middleware
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Session middleware
# Admin va student session'lari shu middleware orqali
# boshqariladi. Mavjud cookie nomi saqlab qolindi.
# --------------------------------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="admin_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=False,
)

# --------------------------------------------------
# Static files and templates
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

# --------------------------------------------------
# Page routes
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request},
    )


@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request):
    return templates.TemplateResponse(
        "quiz.html",
        {"request": request},
    )


@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap_page(request: Request):
    return templates.TemplateResponse(
        "roadmap.html",
        {"request": request},
    )


@app.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    return templates.TemplateResponse(
        "statistics.html",
        {"request": request},
    )


# --------------------------------------------------
# Admin panel authentication
# Bu qism ataylab saqlab qolindi.
# --------------------------------------------------

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

