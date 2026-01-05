from sqlalchemy import Column, Integer, String, Date, Enum, Text, DateTime, Float, ForeignKey, BLOB
from sqlalchemy.orm import relationship
from db import Base
import enum
from datetime import datetime, timedelta


class Admin(Base):
    __tablename__ = "admin"

    admin_id = Column(Integer, primary_key=True, index=True)
    admin_name = Column(String(30), nullable=False)
    password = Column(String(255), nullable=False)
    
    # 이 부분에 관계(relationship)를 추가했습니다.
    sessions = relationship("Session", back_populates="admin")
    logs = relationship("Log", back_populates="admin")
    ships = relationship("Ship", back_populates="admin")


class Passenger(Base):
    __tablename__ = "passenger"

    passenger_id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String(50), nullable=False)
    gender = Column(Enum("M", "F", "Other"))
    job = Column(String(50))
    
    # 암호화된 데이터를 저장할 컬럼 추가
    encrypted_data = Column(BLOB, nullable=False)
    encrypted_aes_key = Column(BLOB, nullable=False)
    admin_id = Column(Integer, ForeignKey("admin.admin_id"), nullable=False)
    admin = relationship("Admin")


class Log(Base):
    __tablename__ = "logs"

    log_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text)
    route_name = Column(String(100))
    reported_at = Column(DateTime, default=datetime.utcnow)
    admin_id = Column(Integer, ForeignKey("admin.admin_id"))
    
    # 이 부분에 관계(relationship)를 추가했습니다.
    admin = relationship("Admin", back_populates="logs")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    start_port = Column(String(100), nullable=False)
    end_port = Column(String(100), nullable=False)


class Waypoint(Base):
    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, nullable=False)
    waypoint_order = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    ship_no = Column(Integer, nullable=False)
    ship_name = Column(String(100), nullable=False)
    departure = Column(Integer, default=0)
    admin_id = Column(Integer, ForeignKey("admin.admin_id"))
    
    # 이 부분에 관계(relationship)를 추가했습니다.
    admin = relationship("Admin", back_populates="ships")


# 이 클래스를 맨 아래에 추가했습니다.
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(255), unique=True, index=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("admin.admin_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # 이 부분에 관계(relationship)를 추가했습니다.
    admin = relationship("Admin", back_populates="sessions")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # created_at이 아직 설정되지 않았을 경우 현재 시간으로 초기화
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        # created_at이 설정된 후에 expires_at 계산
        self.expires_at = self.created_at + timedelta(hours=1)