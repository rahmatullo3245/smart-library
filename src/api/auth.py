import base64
import binascii
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.core.config import settings
from src.db.models import User
from src.db.postgres import AsyncSessionLocal


logger = logging.getLogger(__name__)

# GET /auth/sso
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# POST /api/verify-token
api_router = APIRouter(
    tags=["Authentication API"],
)


class TokenSchema(BaseModel):
    token: str


def verify_laravel_token(token: str) -> dict:
    """
    Laravel yaratgan encoded_payload.signature tokenini
    HMAC-SHA256 orqali tekshiradi va payloadni qaytaradi.
    """

    parts = token.split(".")

    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSO token formati noto'g'ri",
        )

    encoded_data, signature = parts

    expected_signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        encoded_data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSO token imzosi noto'g'ri",
        )

    try:
        padded_data = encoded_data + "=" * (
            (4 - len(encoded_data) % 4) % 4
        )

        decoded_bytes = base64.urlsafe_b64decode(padded_data)
        payload = json.loads(decoded_bytes.decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError("Token payload obyekt bo'lishi kerak")

    except (
        ValueError,
        UnicodeDecodeError,
        binascii.Error,
        json.JSONDecodeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSO token ma'lumotlarini o'qib bo'lmadi",
        )

    return payload


def validate_student_payload(payload: dict) -> tuple[int, str]:
    """Token ichidagi talaba ID va ismini tekshiradi."""

    uid = payload.get("uid")
    fullname = payload.get("fullname")

    if (
        isinstance(uid, bool)
        or not isinstance(uid, (int, str))
        or not str(uid).isdigit()
        or int(uid) <= 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO tokenidagi uid noto'g'ri",
        )

    if not isinstance(fullname, str) or not fullname.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO tokenida fullname mavjud emas",
        )

    return int(uid), fullname.strip()


async def get_or_create_student(uid: int, fullname: str) -> User:
    """
    PostgreSQL'da uid bo'yicha qidiradi.
    Foydalanuvchi yo'q bo'lsa yaratadi.
    Mavjud foydalanuvchini qayta yaratmaydi.
    """

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == uid)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=uid,
                fullname=fullname,
                role="student",
                is_active=True,
            )

            session.add(user)

            try:
                await session.commit()
                await session.refresh(user)

                logger.info(
                    "Yangi talaba PostgreSQL'ga qo'shildi: uid=%s",
                    uid,
                )

            except IntegrityError:
                # Bir vaqtning o'zida kelgan boshqa so'rov
                # shu foydalanuvchini yaratgan bo'lishi mumkin.
                await session.rollback()

                result = await session.execute(
                    select(User).where(User.id == uid)
                )
                user = result.scalar_one_or_none()

                if user is None:
                    logger.exception(
                        "Talabani yaratishda IntegrityError: uid=%s",
                        uid,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Foydalanuvchini bazaga saqlab bo'lmadi",
                    )
        else:
            logger.info(
                "Talaba bazada oldindan mavjud: uid=%s",
                uid,
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ushbu foydalanuvchi faol emas",
            )

        # Kerakli qiymatlarni session yopilishidan oldin olamiz.
        student_id = user.id
        student_name = user.fullname

        # ORM obyektini tashqariga chiqarish o'rniga,
        # session ichida olingan ma'lumotlarni qaytaramiz.
        return {
            "id": student_id,
            "fullname": student_name,
            "role": user.role,
            "is_active": user.is_active,
        }


async def authenticate_student(token: str, request: Request) -> dict:
    """
    Umumiy SSO oqimi:
    1. Tokenni tekshirish.
    2. Payloadni validatsiya qilish.
    3. PostgreSQL'dan foydalanuvchini olish yoki yaratish.
    4. Session'ga yozish.
    """

    payload = verify_laravel_token(token)
    uid, fullname = validate_student_payload(payload)

    user = await get_or_create_student(uid, fullname)

    request.session["student_id"] = user["id"]
    request.session["student_name"] = user["fullname"]

    return {
        **payload,
        "uid": user["id"],
        "fullname": user["fullname"],
    }


@api_router.post("/api/verify-token")
async def api_verify_token(
    data: TokenSchema,
    request: Request,
):
    """
    Frontend ishlatayotgan endpoint.
    Token tekshiriladi va PostgreSQL foydalanuvchisi sinxronlanadi.
    """

    if not data.token or not data.token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token topilmadi",
        )

    user_data = await authenticate_student(data.token, request)

    return {
        "status": "success",
        "user": user_data,
    }


@router.get("/sso")
async def sso_login(
    request: Request,
    token: str = Query(...),
):
    """
    Laravel'dan to'g'ridan-to'g'ri redirect orqali kirish.
    """

    await authenticate_student(token, request)

    return RedirectResponse(
        url="/chat",
        status_code=status.HTTP_302_FOUND,
    )
