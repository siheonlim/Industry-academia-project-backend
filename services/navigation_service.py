from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.tables import Route, Waypoint
from math import radians, sin, cos, sqrt, atan2

async def get_route_geojson(db: AsyncSession, route_id: int):
    print("요청된 route_id:", route_id)

    result = await db.execute(
        select(Waypoint).where(Waypoint.route_id == route_id).order_by(Waypoint.waypoint_order)
    )
    waypoints = result.scalars().all()
    print("조회된 waypoint 수:", len(waypoints))
    if not waypoints:
        return None

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "route_id": route_id
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [wp.longitude, wp.latitude] for wp in waypoints
                    ]
                }
            }
        ]
    }
    return geojson


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 지구 반지름 (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

async def get_route_info(db: AsyncSession, route_id: int):
    result = await db.execute(
        select(Waypoint).where(Waypoint.route_id == route_id).order_by(Waypoint.waypoint_order)
    )
    waypoints = result.scalars().all()
    if not waypoints:
        return None

    total_distance = 0
    for i in range(len(waypoints) - 1):
        total_distance += calculate_distance(
            waypoints[i].latitude, waypoints[i].longitude,
            waypoints[i + 1].latitude, waypoints[i + 1].longitude
        )

    speed_fast = 40
    speed_cargo = 25
    duration_fast = total_distance / speed_fast
    duration_cargo = total_distance / speed_cargo

    route_row = await db.execute(select(Route).where(Route.id == route_id))
    route = route_row.scalar()
    if not route:
        return None

    return {
        "route_id": route_id,
        "departure": route.start_port,
        "arrival": route.end_port,
        "distance": f"{total_distance:.1f} km",
        "duration_fast": f"{duration_fast:.1f} 시간",
        "duration_cargo": f"{duration_cargo:.1f} 시간"
    }
