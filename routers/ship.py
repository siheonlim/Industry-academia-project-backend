from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from services.ship_service import get_all_ships_with_admin, create_ship
from models.schemas import ShipWithAdminOut, ShipCreateRequest
from typing import List

router = APIRouter()

@router.get("/", response_model=List[ShipWithAdminOut])
async def read_ships(db: AsyncSession = Depends(get_db)):
    ships = await get_all_ships_with_admin(db)
    return ships

@router.post("/register")
async def register_ship(request: ShipCreateRequest, db: AsyncSession = Depends(get_db)):
    return await create_ship(
        session=db,
        ship_no=request.ship_no,
        ship_name=request.ship_name,
        admin_name=request.admin_name
    )