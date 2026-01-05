from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.tables import Admin, Session as DBSession
from datetime import datetime, timedelta
import uuid
from sqlalchemy import delete

# 1. 관리자 인증 함수 수정
async def authenticate_admin(session: AsyncSession, admin_name: str, password: str):
    result = await session.execute(
        select(Admin).where(Admin.admin_name == admin_name)
    )
    admin = result.scalars().first()

    if not admin:
        return None 
    
    if admin.password != password:
        return None  

    return admin  

# 2. 세션 생성 함수 추가
async def create_session(session: AsyncSession, admin_id: int):
    """
    새로운 세션 레코드를 생성하고 DB에 저장합니다.
    """
    session_key = str(uuid.uuid4())
    db_session = DBSession(session_key=session_key, admin_id=admin_id)
    
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)
    
    return db_session

# 3. 세션 키로 관리자 정보 조회 함수 추가
async def get_admin_by_session_key(session: AsyncSession, session_key: str):
    result = await session.execute(
        select(DBSession).where(DBSession.session_key == session_key)
    )
    session_record = result.scalars().first()
    
    if session_record and session_record.expires_at > datetime.utcnow():
        return session_record.admin
    return None

# 4. 관리자 등록 함수
async def register_admin(session: AsyncSession, admin_name: str, password: str):
    result = await session.execute(
        select(Admin).where(Admin.admin_name == admin_name)
    )
    existing_admin = result.scalars().first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="이미 존재하는 관리자명입니다.")

    new_admin = Admin(admin_name=admin_name, password=password)
    session.add(new_admin)
    await session.commit()
    await session.refresh(new_admin)

    return {
        "success": True,
        "message": f"{admin_name} 관리자 등록 성공",
        "admin_id": new_admin.admin_id
    }

async def logout_admin(session: AsyncSession, session_key: str):

    # 세션 키에 해당하는 레코드 찾기
    result = await session.execute(
        select(DBSession).where(DBSession.session_key == session_key)
    )
    db_session = result.scalars().first()

    if db_session:
        await session.delete(db_session)
        await session.commit()
        return True
    return False