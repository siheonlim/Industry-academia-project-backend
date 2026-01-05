# /Backend/data_ingestion.py

import pandas as pd
import mysql.connector
from services.encryption_utils import encrypt_sensitive_data
import json
import os
import sys

# MySQL 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'db_password',
    'database': 'db_name'
}

# ------------------------------
# 1. CSV 데이터 불러오기
# ------------------------------
csv_path = "data/passenger_data.csv"
if not os.path.exists(csv_path):
    print(f"[오류] CSV 파일이 존재하지 않습니다. 경로를 확인하세요: {csv_path}")
    sys.exit()

try:
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"[정보] '{csv_path}' 파일에서 데이터를 불러왔습니다.")
    
    # 성별을 M/F로 변환
    df['gender_code'] = df['성별'].apply(lambda x: 'M' if x.strip().lower() == 'male' else 'F' if x.strip().lower() == 'female' else 'Other')
    # 지병여부를 불리언으로 변환
    df['is_sick'] = df['지병여부'].apply(lambda x: True if str(x).strip().lower() == 'true' else False)

except Exception as e:
    print(f"CSV 파일 처리 중 오류 발생: {e}")
    sys.exit()

# ------------------------------
# 2. 데이터베이스 연결 및 삽입
# ------------------------------
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("[정보] MySQL 데이터베이스에 연결되었습니다.")

    # DB에 삽입 쿼리 준비
    query = """
    INSERT INTO passenger (passenger_name, gender, job, encrypted_data, encrypted_aes_key)
    VALUES (%s, %s, %s, %s, %s)
    """

    for index, row in df.iterrows():
        # 암호화 대상 데이터 (생년월일, 전화번호, 지병여부)
        data_to_encrypt = {
            '생년월일': str(row['생년월일']), # Pydantic date가 아니므로 문자열로 처리
            '전화번호': str(row['전화번호']),
            '지병여부': row['is_sick']
        }
        
        # services/encryption_utils.py의 함수를 사용하여 데이터 암호화
        encrypted_blobs = encrypt_sensitive_data(data_to_encrypt)
        
        # DB에 삽입할 튜플 준비
        data_tuple = (
            row['이름'],
            row['gender_code'],
            row['직업'],
            encrypted_blobs['encrypted_data'],
            encrypted_blobs['encrypted_aes_key']
        )
        
        cur.execute(query, data_tuple)

    conn.commit()
    print("[성공] 모든 데이터가 성공적으로 암호화되어 DB에 저장되었습니다.")

except mysql.connector.Error as err:
    print(f"MySQL 연결 또는 삽입 오류: {err}")
    conn.rollback() # 오류 발생 시 롤백
except Exception as e:
    print(f"데이터 처리 중 예상치 못한 오류 발생: {e}")
    conn.rollback()
finally:
    if 'conn' in locals() and conn.is_connected():
        cur.close()
        conn.close()
        print("MySQL 연결이 닫혔습니다.")
