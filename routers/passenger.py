# /routers/passenger.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from services.passenger_service import get_passenger_by_id, get_all_passengers_decrypted,process_and_save_csv
from models.schemas import PassengerOut
from typing import List

router = APIRouter()

# 기존 라우터: 특정 승객 조회
@router.get("/{passenger_id}", response_model=PassengerOut)
async def read_passenger(passenger_id: int, db: AsyncSession = Depends(get_db)):
    """특정 승객의 정보를 복호화하여 반환합니다."""
    passenger = await get_passenger_by_id(db, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")
    return passenger

# 새로 추가할 라우터: 모든 승객 조회
@router.get("/", response_model=List[PassengerOut])
async def read_all_passengers(
    admin_id: int = Query(..., description="로그인한 관리자의 ID"), # Query로 변경
    db: AsyncSession = Depends(get_db)
):
    """
    모든 승객의 복호화된 정보를 반환합니다.
    """
    return await get_all_passengers_decrypted(db, admin_id)

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...), 
    admin_id: int = Form(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    CSV 파일을 업로드하여 승객 정보를 암호화하고 DB에 저장합니다.
    """
    try:
        # 파일 내용을 읽음
        file_data = await file.read()
        
        # 서비스 함수 호출
        result = await process_and_save_csv(db, file_data, admin_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류 발생: {e}")