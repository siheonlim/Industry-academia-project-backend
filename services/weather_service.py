import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.tables import Waypoint
from datetime import datetime, timedelta, timezone
import pytz

WEATHER_API_KEY = "WEATHER_API_KEY"

# 현재 날씨 조회 (current.json)
async def fetch_weather_by_route(session: AsyncSession, route_id: int):
    result = await session.execute(
        select(Waypoint).where(Waypoint.route_id == route_id).order_by(Waypoint.waypoint_order)
    )
    waypoints = result.scalars().all()

    if not waypoints:
        return {"error": "해당 경로의 waypoint를 찾을 수 없습니다."}

    url = "https://api.weatherapi.com/v1/current.json"
    weather_results = []

    async with httpx.AsyncClient() as client:
        for wp in waypoints:
            q_param = f"{round(wp.latitude, 4)},{round(wp.longitude, 4)}"
            params = {
                "key": WEATHER_API_KEY,
                "q": q_param,
                "aqi": "no"
            }
            try:
                response = await client.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()

                data["waypoint_order"] = wp.waypoint_order
                data["latitude"] = wp.latitude
                data["longitude"] = wp.longitude
                weather_results.append(data)

            except httpx.HTTPStatusError as e:
                logging.warning(f"[WeatherAPI 400] {q_param}: {e.response.text}")
                weather_results.append({
                    "waypoint_order": wp.waypoint_order,
                    "latitude": wp.latitude,
                    "longitude": wp.longitude,
                    "error": f"HTTP {e.response.status_code}: {e.response.text}"
                })
            except httpx.RequestError as e:
                logging.error(f"[WeatherAPI Error] {q_param}: {str(e)}")
                weather_results.append({
                    "waypoint_order": wp.waypoint_order,
                    "latitude": wp.latitude,
                    "longitude": wp.longitude,
                    "error": f"Request failed: {str(e)}"
                })

    return {"route_id": route_id, "weather": weather_results}


# 시간 offset 기준 예보 조회 (forecast.json)
async def fetch_forecast_by_route(session: AsyncSession, route_id: int, offset: int):
    result = await session.execute(
        select(Waypoint).where(Waypoint.route_id == route_id).order_by(Waypoint.waypoint_order)
    )
    waypoints = result.scalars().all()

    if not waypoints:
        return {"error": "해당 경로의 waypoint를 찾을 수 없습니다."}

    url = "https://api.weatherapi.com/v1/forecast.json"
    weather_results = []

    # 현재시간(KST) + offset 계산 → UTC 변환
    now_kst = datetime.now(pytz.timezone("Asia/Seoul"))
    target_kst = now_kst + timedelta(hours=offset)
    target_kst = target_kst.replace(minute=0, second=0, microsecond=0)
    target_utc = target_kst.astimezone(pytz.utc)

    print(f"[DEBUG] 현재 KST: {now_kst}, 타겟 KST: {target_kst}, 타겟 UTC: {target_utc}")

    async with httpx.AsyncClient() as client:
        for wp in waypoints:
            q_param = f"{round(wp.latitude, 4)},{round(wp.longitude, 4)}"
            params = {
                "key": WEATHER_API_KEY,
                "q": q_param,
                "days": 2,
                "aqi": "no"
            }
            try:
                response = await client.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()

                forecast_days = data.get("forecast", {}).get("forecastday", [])
                all_hours = []
                for day in forecast_days:
                    all_hours.extend(day.get("hour", []))

                if not all_hours:
                    raise ValueError("Hourly forecast not found.")

                closest = min(
                    all_hours,
                    key=lambda h: abs(
                        datetime.strptime(h["time"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) - target_utc
                    )
                )

                weather_results.append({
                    "waypoint_order": wp.waypoint_order,
                    "latitude": wp.latitude,
                    "longitude": wp.longitude,
                    "location": data.get("location", {}),
                    "current": closest,
                    "is_danger": closest["wind_kph"] > 30,
                })

            except Exception as e:
                logging.warning(f"[WeatherAPI Forecast Error] {q_param}: {e}")
                weather_results.append({
                    "waypoint_order": wp.waypoint_order,
                    "latitude": wp.latitude,
                    "longitude": wp.longitude,
                    "error": str(e)
                })

    return {
        "route_id": route_id,
        "offset": offset,
        "target_hour_kst": target_kst.strftime("%Y-%m-%d %H:%M:%S"),
        "target_hour_utc": target_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "weather": weather_results
    }

