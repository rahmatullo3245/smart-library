from sqladmin import ModelView
from wtforms import PasswordField, StringField
from wtforms.validators import Optional, DataRequired, EqualTo


from src.db.models import (
    User,
    ChatSession,
    ChatMessage,
    Book,
    BookChunk,
    AdminUser
)

from src.core.security import hash_password


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.fullname,
        User.role,
        User.is_active,
        User.created_at,
        User.updated_at,
    ]

    column_searchable_list = [
        User.fullname,
    ]

    column_sortable_list = [
        User.id,
        User.fullname,
        User.role,
        User.created_at,
        User.updated_at,
    ]

    column_default_sort = [
        (User.created_at, True),
    ]


class ChatSessionAdmin(ModelView, model=ChatSession):
    name = "Chat Session"
    name_plural = "Chat Sessions"
    icon = "fa-solid fa-comments"

    column_list = [
        ChatSession.id,
        ChatSession.user,
        ChatSession.title,
        ChatSession.created_at,
        ChatSession.updated_at,
    ]

    column_searchable_list = [
        ChatSession.title,
    ]

    column_sortable_list = [
        ChatSession.created_at,
        ChatSession.updated_at,
    ]

    column_default_sort = [
        (ChatSession.created_at, True),
    ]


class ChatMessageAdmin(ModelView, model=ChatMessage):
    name = "Chat Message"
    name_plural = "Chat Messages"
    icon = "fa-solid fa-message"

    column_list = [
        ChatMessage.id,
        ChatMessage.session,
        ChatMessage.role,
        ChatMessage.content,
        ChatMessage.tokens_used,
        ChatMessage.created_at,
    ]

    column_searchable_list = [
        ChatMessage.content,
        ChatMessage.role,
    ]

    column_sortable_list = [
        ChatMessage.id,
        ChatMessage.tokens_used,
        ChatMessage.created_at,
    ]

    column_default_sort = [
        (ChatMessage.created_at, True),
    ]


class BookAdmin(ModelView, model=Book):
    name = "Book"
    name_plural = "Books"
    icon = "fa-solid fa-book"

    column_list = [
        Book.id,
        Book.title,
        Book.file_type,
        Book.status,
        Book.uploader,
        Book.created_at,
    ]

    column_searchable_list = [
        Book.title,
        Book.file_path,
        Book.file_type,
        Book.status,
    ]

    column_sortable_list = [
        Book.id,
        Book.title,
        Book.file_type,
        Book.status,
        Book.created_at,
    ]

    column_default_sort = [
        (Book.created_at, True),
    ]


class BookChunkAdmin(ModelView, model=BookChunk):
    name = "Book Chunk"
    name_plural = "Book Chunks"
    icon = "fa-solid fa-puzzle-piece"

    column_list = [
        BookChunk.id,
        BookChunk.book,
        BookChunk.chunk_index,
        BookChunk.page_number,
        BookChunk.content,
    ]

    column_searchable_list = [
        BookChunk.content,
    ]

    column_sortable_list = [
        BookChunk.id,
        BookChunk.chunk_index,
        BookChunk.page_number,
    ]

    column_default_sort = [
        (BookChunk.id, True),
    ]
class AdminUserAdmin(ModelView, model=AdminUser):
    name = "Admin User"
    name_plural = "Admin Users"
    icon = "fa-solid fa-user-shield"

    # =========================================================
    # LIST
    # =========================================================

    column_list = [
        AdminUser.id,
        AdminUser.username,
        AdminUser.fullname,
        AdminUser.is_active,
        AdminUser.is_superadmin,
        AdminUser.created_at,
        AdminUser.updated_at,
    ]

    column_searchable_list = [
        AdminUser.username,
        AdminUser.fullname,
    ]

    column_sortable_list = [
        AdminUser.id,
        AdminUser.username,
        AdminUser.fullname,
        AdminUser.is_active,
        AdminUser.is_superadmin,
        AdminUser.created_at,
        AdminUser.updated_at,
    ]

    column_default_sort = [
        (AdminUser.created_at, True),
    ]

    # =========================================================
    # FORM
    # =========================================================

    # DBdagi password_hash hech qachon formda ko'rinmaydi.
    form_excluded_columns = [
        AdminUser.password_hash,
        AdminUser.created_at,
        AdminUser.updated_at,
    ]

    # =========================================================
    # CUSTOM FORM
    # =========================================================

    async def scaffold_form(self, rules=None):
        """
        SQLAdmin avtomatik yaratgan formga
        password va password_confirm fieldlarini qo'shamiz.
        """

        form_class = await super().scaffold_form(rules)

        # Password
        form_class.password = PasswordField(
            "Password",
            validators=[
                Optional(),
                EqualTo(
                    "password_confirm",
                    message="Passwordlar bir xil emas!",
                ),
            ],
            render_kw={
                "autocomplete": "new-password",
                "placeholder": "Password",
            },
        )

        # Confirm Password
        form_class.password_confirm = PasswordField(
            "Confirm Password",
            validators=[
                Optional(),
            ],
            render_kw={
                "autocomplete": "new-password",
                "placeholder": "Confirm password",
            },
        )

        return form_class

    # =========================================================
    # CREATE / EDIT
    # =========================================================

    async def on_model_change(
        self,
        data: dict,
        model: AdminUser,
        is_created: bool,
        request,
    ):
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        # -----------------------------------------------------
        # CREATE
        # -----------------------------------------------------

        if is_created:

            if not password:
                raise ValueError(
                    "Yangi admin uchun password kiritish majburiy!"
                )

            if not password_confirm:
                raise ValueError(
                    "Confirm Password kiritish majburiy!"
                )

            if password != password_confirm:
                raise ValueError(
                    "Passwordlar bir xil emas!"
                )

            # Plain password DBga yozilmaydi.
            model.password_hash = hash_password(password)

        # -----------------------------------------------------
        # EDIT
        # -----------------------------------------------------

        else:

            # Edit vaqtida password bo'sh bo'lsa,
            # eski password o'zgarishsiz qoladi.

            if password:

                if not password_confirm:
                    raise ValueError(
                        "Confirm Password kiritish majburiy!"
                    )

                if password != password_confirm:
                    raise ValueError(
                        "Passwordlar bir xil emas!"
                    )

                model.password_hash = hash_password(password)