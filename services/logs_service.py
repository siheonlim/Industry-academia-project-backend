from sqlalchemy import select
from sqlalchemy.orm import aliased
from models.tables import Log, Admin
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def get_all_logs(db: AsyncSession):
    query = (
        select(
            Log.log_id,
            Log.title,
            Log.content,
            Log.route_name,
            Log.reported_at,
            Admin.admin_name  # ← admin_name 추가
        )
        .join(Admin, Log.admin_id == Admin.admin_id)
        .order_by(Log.reported_at.desc())
    )

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        {
            "log_id": row.log_id,
            "title": row.title,
            "content": row.content,
            "route_name": row.route_name,
            "reported_at": row.reported_at,
            "admin_name": row.admin_name  # ← 포함
        }
        for row in rows
    ]

async def create_log_by_headquarter(session: AsyncSession, title: str, content: str, route_name: str, admin_id: int):
    new_log = Log(
        title=title,
        content=content,
        route_name=route_name,
        reported_at=datetime.utcnow(),
        admin_id=admin_id 
    )
    session.add(new_log)
    await session.commit()
    await session.refresh(new_log)
    return new_log