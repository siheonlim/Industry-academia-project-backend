from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.navigation_service import get_route_geojson, get_route_info
from db import get_db

router = APIRouter()

@router.get("/routes/{route_id}")
async def get_route(route_id: int, db: AsyncSession = Depends(get_db)):
    geojson = await get_route_geojson(db, route_id)
    if not geojson:
        raise HTTPException(status_code=404, detail="Route not found")
    return geojson

@router.get("/routes/{route_id}/info")
async def get_route_info_api(route_id: int, db: AsyncSession = Depends(get_db)):
    info = await get_route_info(db, route_id)
    if not info:
        raise HTTPException(status_code=404, detail="Route info not found")
    return info
