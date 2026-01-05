from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

# 로그인 요청을 위한 스키마
class AdminLogin(BaseModel):
    admin_name: str
    password: str


# 로그인 성공 시 세션 키를 반환하는 스키마
class Token(BaseModel):
    session_key: str
    admin_id: int

# 탑승객 출력용
class PassengerOut(BaseModel):
    passenger_id: int
    passenger_name: str
    birth: Optional[date]
    gender: Optional[str]
    contact: Optional[str]
    special_needs: Optional[bool]
    job: Optional[str]

    class Config:
        orm_mode = True

# 로그 출력용
class LogOut(BaseModel):
    log_id: int
    title: str
    content: Optional[str]
    route_name: Optional[str]
    reported_at: datetime
    admin_name: str

    class Config:
        orm_mode = True

class HeadLogCreateRequest(BaseModel):
    title: str
    content: str
    route_name: str
    admin_id: int  

class LogResponse(BaseModel):
    log_id: int
    title: str
    content: str
    route_name: str
    reported_at: datetime
    admin_id: int

    class Config:
        orm_mode = True

class AdminRegisterRequest(BaseModel):
    admin_name: str
    password: str

class AdminRegisterResponse(BaseModel):
    success: bool
    message: str
    admin_id: int


class ShipOut(BaseModel):
    id: int
    ship_no: int
    ship_name: str
    departure: int
    admin_id: Optional[int]

    class Config:
        orm_mode = True

class ShipWithAdminOut(BaseModel):
    id: int
    ship_no: int
    ship_name: str
    departure: int
    admin_name: Optional[str]

    class Config:
        orm_mode = False  # 직접 dict 생성하므로 orm_mode는 False

class ShipCreateRequest(BaseModel):
    ship_no: int
    ship_name: str
    admin_name: str