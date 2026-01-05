# /services/passenger_service.py

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.tables import Passenger
from models.schemas import PassengerOut
from services.encryption_utils import decrypt_sensitive_data
from typing import Optional, List
from datetime import date
from services.encryption_utils import encrypt_sensitive_data, decrypt_sensitive_data
import io
import pandas as pd

# 파라미터로 승객 조회
async def get_passenger_by_id(db: AsyncSession, passenger_id: int) -> Optional[PassengerOut]:
    result = await db.execute(select(Passenger).filter(Passenger.passenger_id == passenger_id))
    passenger = result.scalar_one_or_none()
    
    if not passenger:
        return None

    # 암호화된 데이터 복호화
    decrypted_data = decrypt_sensitive_data(
        passenger.encrypted_data,
        passenger.encrypted_aes_key
    )
    
    if not decrypted_data:
        # 복호화 실패 시, 적절한 오류 처리
        return None

    # 복호화된 데이터와 평문 데이터를 결합
    return PassengerOut(
        passenger_id=passenger.passenger_id,
        passenger_name=passenger.passenger_name,
        gender=passenger.gender,
        job=passenger.job,
        birth=decrypted_data.get('생년월일'),
        contact=decrypted_data.get('전화번호'),
        special_needs=decrypted_data.get('지병여부')
    )

# 승객 조회
async def get_all_passengers_decrypted(db: AsyncSession, admin_id:int) -> List[PassengerOut]:
    """모든 승객의 정보를 복호화하여 리스트로 반환합니다."""
    
    result = await db.execute(select(Passenger).filter(Passenger.admin_id == admin_id))
    passengers = result.scalars().all()
    
    decrypted_passengers = []
    for p in passengers:
        decrypted_data = decrypt_sensitive_data(
            p.encrypted_data,
            p.encrypted_aes_key
        )
        
        if decrypted_data:
            decrypted_passengers.append(PassengerOut(
                passenger_id=p.passenger_id,
                passenger_name=p.passenger_name,
                gender=p.gender,
                job=p.job,
                birth=decrypted_data.get('생년월일'),
                contact=decrypted_data.get('전화번호'),
                special_needs=decrypted_data.get('지병여부')
            ))
            
    return decrypted_passengers


async def process_and_save_csv(db: AsyncSession, file_data: bytes, admin_id: int):
    """
    업로드된 CSV 파일을 읽고, 해당 관리자의 기존 데이터를 삭제한 후 DB에 일괄 저장합니다.
    """
    try:
        # admin_id에 해당하는 기존 승객 데이터만 삭제
        await db.execute(delete(Passenger).filter(Passenger.admin_id == admin_id))
        await db.commit()
        print(f"[정보] 관리자 ID {admin_id}가 등록한 기존 승객 데이터가 삭제되었습니다.")
        
        df = pd.read_csv(io.BytesIO(file_data), encoding='utf-8')
        
        df['gender_code'] = df['성별'].apply(lambda x: 'M' if x.strip().lower() == 'male' else 'F' if x.strip().lower() == 'female' else 'Other')
        df['is_sick'] = df['지병여부'].apply(lambda x: True if str(x).strip().lower() == 'true' else False)
        
        passenger_list = []
        for index, row in df.iterrows():
            sensitive_data = {
                '생년월일': str(row['생년월일']),
                '전화번호': str(row['전화번호']),
                '지병여부': row['is_sick']
            }
            
            encrypted_blobs = encrypt_sensitive_data(sensitive_data)
            
            new_passenger = Passenger(
                passenger_name=row['이름'],
                gender=row['gender_code'],
                job=row['직업'],
                encrypted_data=encrypted_blobs['encrypted_data'],
                encrypted_aes_key=encrypted_blobs['encrypted_aes_key'],
                admin_id=admin_id
            )
            passenger_list.append(new_passenger)

        db.add_all(passenger_list)
        await db.commit()
        return {"status": "success", "message": f"{len(passenger_list)}명의 승객 데이터가 성공적으로 저장되었습니다."}

    except Exception as e:
        await db.rollback()
        raise e