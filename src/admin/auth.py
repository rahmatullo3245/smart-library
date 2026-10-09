from fastapi import Request
from sqlalchemy import select
from sqladmin.authentication import AuthenticationBackend

from src.db.models import AdminUser
from src.db.postgres import AsyncSessionLocal
from src.core.security import verify_password


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()

        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AdminUser).where(
                    AdminUser.username == username,
                    AdminUser.is_active == True,
                )
            )

            admin_user = result.scalar_one_or_none()

            if not admin_user:
                return False

            if not verify_password(
                password,
                admin_user.password_hash,
            ):
                return False

            # Session'ga admin ID yozamiz
            request.session.update(
                {
                    "admin_user_id": admin_user.id,
                    "admin_username": admin_user.username,
                    "admin_is_superadmin": admin_user.is_superadmin,
                }
            )

            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_user_id = request.session.get("admin_user_id")

        if not admin_user_id:
            return False

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AdminUser).where(
                    AdminUser.id == admin_user_id,
                    AdminUser.is_active == True,
                )
            )

            admin_user = result.scalar_one_or_none()

            return admin_user is not None
