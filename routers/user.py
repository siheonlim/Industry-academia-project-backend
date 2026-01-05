from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.schemas import AdminLogin, Token, AdminRegisterRequest, AdminRegisterResponse
from services.user_service import authenticate_admin, create_session, register_admin
from db import get_db
from fastapi.security import OAuth2PasswordBearer
from services.user_service import logout_admin 

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: AdminLogin,
    session: AsyncSession = Depends(get_db)
):

    admin = await authenticate_admin(session, login_data.admin_name, login_data.password)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    db_session = await create_session(session, admin.admin_id)
    print("데이터 베이스 세션 변수 확인: ",db_session)
    
    return {"session_key": db_session.session_key,  "admin_id": db_session.admin_id}

@router.post("/register", response_model=AdminRegisterResponse)
async def register_admin_endpoint(
    register_data: AdminRegisterRequest,
    session: AsyncSession = Depends(get_db)
):
    return await register_admin(
        session,
        admin_name=register_data.admin_name,
        password=register_data.password
    )

@router.post("/logout")
async def logout_current_admin(
    session_key: str = Depends(OAuth2PasswordBearer(tokenUrl="/login")),
    session: AsyncSession = Depends(get_db)
):
    success = await logout_admin(session, session_key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="로그아웃 실패: 유효한 세션을 찾을 수 없습니다."
        )
    
    return {"message": "로그아웃 성공"}