from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import SessionLocal
from services.logs_service import get_all_logs, create_log_by_headquarter
from models.schemas import LogOut, LogResponse, HeadLogCreateRequest
from typing import List
from models.tables import Log

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

# 모든 로그 조회
@router.get("/", response_model=List[LogOut])
async def read_logs(db: AsyncSession = Depends(get_db)):
    return await get_all_logs(db)

# 로그 등록
@router.post("/head", response_model=LogResponse)
async def create_log_head(log_data: HeadLogCreateRequest, db: AsyncSession = Depends(get_db)):
    new_log = await create_log_by_headquarter(
        session=db,
        title=log_data.title,
        content=log_data.content,
        route_name=log_data.route_name,
        admin_id=log_data.admin_id
    )
    return new_log

@router.post("/enroll", response_model=LogResponse)
async def create_head_log(
    log_data: HeadLogCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    new_log = Log(
        title=log_data.title,
        content=log_data.content,
        route_name=log_data.route_name,
        admin_id=log_data.admin_id #
    )
    session.add(new_log)
    await session.commit()
    await session.refresh(new_log)

    return new_log