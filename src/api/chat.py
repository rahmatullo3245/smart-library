
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, ChatSession, ChatMessage
from src.db.postgres import get_db

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    session_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    message_id: int
    message: str
    status: str


async def get_current_student(
    request: Request,
    db: AsyncSession,
) -> User:
    student_id = request.session.get("student_id")

    if student_id is None:
        raise HTTPException(
            status_code=401,
            detail="Avval Laravel orqali tizimga kiring",
        )

    result = await db.execute(
        select(User).where(
            User.id == student_id,
            User.is_active.is_(True),
        )
    )
    student = result.scalar_one_or_none()

    if student is None:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="Talaba topilmadi yoki faol emas",
        )

    return student


@router.post("", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    student = await get_current_student(request, db)

    message_text = data.message.strip()
    if not message_text:
        raise HTTPException(
            status_code=422,
            detail="Xabar bo'sh bo'lmasligi kerak",
        )

    if data.session_id is not None:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == data.session_id,
                ChatSession.user_id == student.id,
            )
        )
        chat_session = result.scalar_one_or_none()

        if chat_session is None:
            raise HTTPException(
                status_code=404,
                detail="Suhbat topilmadi",
            )
    else:
        chat_session = ChatSession(
            user_id=student.id,
            title=message_text[:80],
        )
        db.add(chat_session)
        await db.flush()

    user_message = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content=message_text,
    )
    db.add(user_message)

    try:
        await db.commit()
        await db.refresh(user_message)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Xabarni bazaga saqlashda xatolik",
        )

    return ChatResponse(
        session_id=chat_session.id,
        message_id=user_message.id,
        message="Xabaringiz saqlandi. AI javobi hali ulanmagan.",
        status="saved",
    )


@router.get("/sessions")
async def list_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    student = await get_current_student(request, db)

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == student.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "title": item.title,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in sessions
    ]


@router.get("/{session_id}/messages")
async def list_messages(
    session_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    student = await get_current_student(request, db)

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == student.id,
        )
    )
    chat_session = result.scalar_one_or_none()

    if chat_session is None:
        raise HTTPException(
            status_code=404,
            detail="Suhbat topilmadi",
        )

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    )
    messages = result.scalars().all()

    return [
        {
            "id": item.id,
            "role": item.role,
            "content": item.content,
            "created_at": item.created_at,
        }
        for item in messages
    ]