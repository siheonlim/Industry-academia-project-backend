# /services/encryption_utils.py

import json
import base64
import os
import sys
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

# RSA 키 파일 경로 설정
PRIVATE_KEY_PATH = "keys/rsa_private.pem"
PUBLIC_KEY_PATH = "keys/rsa_public.pem"

# RSA 키 로드 (KMS 역할 시뮬레이션)
try:
    with open(PRIVATE_KEY_PATH, "rb") as f:
        PRIVATE_KEY = f.read()
    with open(PUBLIC_KEY_PATH, "rb") as f:
        PUBLIC_KEY = f.read()
except IOError as e:
    print(f"[오류] RSA 키 파일을 불러오는 데 실패했습니다: {e}")
    print(f"경로를 확인하세요: {PRIVATE_KEY_PATH}, {PUBLIC_KEY_PATH}")
    sys.exit()

def encrypt_sensitive_data(data: dict):
    """
    민감 데이터를 AES로 암호화하고, AES 키는 RSA 공개 키로 암호화합니다.
    """
    aes_key = get_random_bytes(32)  # 256-bit AES
    
    data_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data_bytes)
    
    aes_encrypted = {
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
        'nonce': base64.b64encode(cipher.nonce).decode('utf-8'),
        'tag': base64.b64encode(tag).decode('utf-8')
    }
    
    rsa_cipher = PKCS1_OAEP.new(RSA.import_key(PUBLIC_KEY))
    encrypted_aes_key = rsa_cipher.encrypt(aes_key)
    
    return {
        'encrypted_data': json.dumps(aes_encrypted).encode('utf-8'),
        'encrypted_aes_key': base64.b64encode(encrypted_aes_key)
    }

def decrypt_sensitive_data(encrypted_data_blob: bytes, encrypted_aes_key_blob: bytes):
    """
    암호화된 데이터를 RSA 개인 키로 복호화합니다.
    """
    try:
        rsa_cipher = PKCS1_OAEP.new(RSA.import_key(PRIVATE_KEY))
        encrypted_aes_key = base64.b64decode(encrypted_aes_key_blob)
        aes_key = rsa_cipher.decrypt(encrypted_aes_key)

        enc_data_decoded = json.loads(encrypted_data_blob.decode('utf-8'))
        enc_data = {k: base64.b64decode(v) for k, v in enc_data_decoded.items()}
        
        cipher = AES.new(aes_key, AES.MODE_EAX, nonce=enc_data['nonce'])
        data_bytes = cipher.decrypt_and_verify(enc_data['ciphertext'], enc_data['tag'])
        
        return json.loads(data_bytes.decode('utf-8'))
    except Exception as e:
        print(f"복호화 중 오류 발생: {e}")
        return None