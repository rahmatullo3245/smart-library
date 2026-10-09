from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# User Schemas
class UserBase(BaseModel):
    id: int
    fullname: str
    role: Optional[str] = "student"

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Chat Schemas
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    session_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


# Book Schemas
class BookResponse(BaseModel):
    id: int
    title: str
    file_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True