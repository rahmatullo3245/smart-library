import jwt
from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import RedirectResponse
from src.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/sso")
async def sso_login(token: str = Query(...)):
    """
    Laravel'dan 'Ask AI' tugmasi orqali o'tganda student ma'lumotlarini
    token ichidan o'qib, avtomatik login qiluvchi endpoint.
    """
    try:
        # Tokenni Laravel bilan umumiy bo'lgan Secret Key orqali deshifrovka qilamiz
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="SSO token vaqti o'tib ketgan"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Yaroqsiz SSO token"
        )

    student_id = payload.get("student_id")
    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")

    if not student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token ichida student_id topilmadi"
        )

    # Student ma'lumotlari bilan AI Chat sahifasiga yo'naltiramiz
    response = RedirectResponse(url="/chat", status_code=302)

    # Brauzer cookie-siga student ID va ismini saqlaymiz
    response.set_cookie(
        key="student_id",
        value=str(student_id),
        httponly=True,
        samesite="lax"
    )
    response.set_cookie(
        key="student_name",
        value=f"{first_name} {last_name}".strip(),
        httponly=False,
        samesite="lax"
    )

    return response