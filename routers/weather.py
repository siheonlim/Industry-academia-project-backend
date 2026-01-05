from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from services.weather_service import (
    fetch_weather_by_route,
    fetch_forecast_by_route
)
from db import get_db

router = APIRouter()

# 현재 날씨 조회 
@router.get("/route/{route_id}")
async def get_weather_by_route(route_id: int, session: AsyncSession = Depends(get_db)):
    return await fetch_weather_by_route(session, route_id)

# 예보 조회 - offset 시간 기준 (시간 단위 예: 4, -6, 12 등)
@router.get("/route/{route_id}/forecast")
async def get_forecast_by_route(
    route_id: int,
    offset: int = Query(..., description="현재 기준 offset 시간 (시간 단위, 예: 4, -6)"),
    session: AsyncSession = Depends(get_db)
):
    print(f"📡 Received route_id={route_id}, offset={offset}")
    return await fetch_forecast_by_route(session, route_id, offset)
