from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import logs, passenger, weather, navigation, user, ship
from db import engine, Base

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 전체 허용, 배포 시 도메인 지정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(weather.router, prefix="/weather", tags=["Weather"])
app.include_router(passenger.router, prefix="/passenger", tags=["Passenger"])
app.include_router(navigation.router, prefix="/navigation", tags=["Navigation"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(ship.router, prefix="/ship", tags=["ship"])


@app.get("/")
def root():
    return {"message": "Ocean 백엔드 서버가 정상 작동 중입니다."}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
