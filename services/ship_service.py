from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound
from models.tables import Ship, Admin
from fastapi import HTTPException

async def get_all_ships_with_admin(session: AsyncSession):
    result = await session.execute(
        select(Ship, Admin.admin_name)
        .join(Admin, Ship.admin_id == Admin.admin_id, isouter=True)  # LEFT OUTER JOIN
    )
    rows = result.all()
    ships = []
    for ship, admin_name in rows:
        ship_dict = {
            "id": ship.id,
            "ship_no": ship.ship_no,
            "ship_name": ship.ship_name,
            "departure": ship.departure,
            "admin_name": admin_name
        }
        ships.append(ship_dict)
    return ships

async def create_ship(session: AsyncSession, ship_no: int, ship_name: str, admin_name: str):
    # 1. 관리자 존재 여부 확인
    result = await session.execute(
        select(Admin).where(Admin.admin_name == admin_name)
    )
    admin = result.scalars().first()

    if not admin:
        raise HTTPException(status_code=404, detail="담당 관리자명을 찾을 수 없습니다.")

    # 2. 선박 생성
    new_ship = Ship(
        ship_no=ship_no,
        ship_name=ship_name,
        departure=0,  # 기본값: 미출항
        admin_id=admin.admin_id
    )
    session.add(new_ship)
    await session.commit()
    await session.refresh(new_ship)

    return {
        "success": True,
        "message": "선박이 등록되었습니다.",
        "ship_id": new_ship.id
    }