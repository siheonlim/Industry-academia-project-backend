## BackEnd README

### 1. 프로젝트 개요

이 디렉터리는 선박 운항/승객·로그 관리·항로/날씨 정보를 제공하는 **FastAPI 기반 백엔드 서버**입니다.  
관리자 계정으로 로그인하여 선박과 항로를 관리하고, 특정 항로에 대한 실시간/예보 날씨 정보를 조회할 수 있습니다.

>  **중요**  
> GitHub에 올라가는 버전에서는 **데이터베이스 접속 정보(`data_ingestion.py`, `db.py`)와 날씨 API 키(`services/weather_service.py`)가 모두 제거**되어 있습니다.  
> 따라서 **배포 시나 로컬 실행 시, 직접 환경변수 또는 별도 설정 파일로 값을 채워 넣어야** 시스템이 정상 동작합니다.

---

### 2. 폴더 구조

```text
BackEnd/
  ├─ main.py                 # FastAPI 앱 진입점
  ├─ db.py                   # 비동기 SQLAlchemy 엔진/세션 설정 (MySQL)
  ├─ data_ingestion.py       # CSV 승객 데이터 → 암호화 후 DB 적재 스크립트
  ├─ models/
  │   ├─ tables.py           # SQLAlchemy ORM 모델 정의 (Admin, Passenger, Ship, Route, Waypoint 등)
  │   └─ schemas.py          # Pydantic 스키마 정의 (API I/O 모델)
  ├─ routers/
  │   ├─ user.py             # 관리자 로그인/회원가입/로그아웃 API
  │   ├─ ship.py             # 선박 정보 조회/등록 API
  │   ├─ navigation.py       # 항로 GeoJSON 및 거리/소요 시간 정보 API
  │   ├─ passenger.py        # 승객 조회 및 CSV 업로드 API
  │   ├─ weather.py          # 항로 기준 현재 날씨/예보 조회 API
  │   └─ logs.py             # 운항/상황 로그 관련 API
  ├─ services/
  │   ├─ user_service.py         # 관리자 인증/세션 로직
  │   ├─ ship_service.py         # 선박 비즈니스 로직
  │   ├─ navigation_service.py   # 항로 및 거리 계산 로직
  │   ├─ passenger_service.py    # 승객 암·복호화 및 CSV 처리 로직
  │   ├─ logs_service.py         # 로그 비즈니스 로직
  │   ├─ weather_service.py      # 외부 Weather API 연동 로직
  │   └─ encryption_utils.py     # 개인 정보 암·복호화 유틸
  ├─ keys/                    # 암호화 키(예: RSA 키쌍) 보관 디렉터리 (Git에 올리지 않는 것을 권장)
  └─ public/                  # 정적 리소스 또는 공개용 파일 (있다면)
```

---

### 3. 주요 기술 스택 & 외부 모듈

- **프레임워크**
  - **FastAPI**: 비동기 Python 웹 프레임워크
  - **Uvicorn**: ASGI 서버

- **데이터베이스 & ORM**
  - **MySQL**
  - **SQLAlchemy (비동기)**: `sqlalchemy.ext.asyncio`, `aiomysql`

- **데이터 처리 / 유틸**
  - **pandas**: CSV 승객 데이터 로딩/전처리 (`data_ingestion.py` 및 CSV 업로드)
  - **mysql-connector-python**: 동기 MySQL 연결 (`data_ingestion.py`)
  - **httpx**: 비동기 HTTP 클라이언트 (Weather API 호출)
  - **pytz / datetime**: 타임존 및 시간 계산 (예보 시각 매칭)
  - **암호화 관련 모듈**: `cryptography` 등 (구체 구현은 `encryption_utils.py` 참고)

- **FastAPI 관련**
  - `python-multipart` (파일 업로드용, 예: `/passenger/upload-csv`)
  - `fastapi.middleware.cors.CORSMiddleware` (CORS 설정)

>  **Weather API 및 DB 연결은 외부 서비스에 강하게 의존**하므로,  
> API 키 또는 DB 접속 정보가 올바로 설정되지 않으면 일부/전체 기능이 정상적으로 작동하지 않을 수 있습니다.

---

### 4. 실행 전 사전 준비

#### 4-1. Python & 가상환경

- **Python 3.10 이상**(권장)을 설치합니다.
- (선택) 가상환경을 생성합니다.

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

#### 4-2. 패키지 설치

`requirements.txt`가 있다면 다음과 같이 설치합니다.

```bash
pip install -r requirements.txt
```

만약 없다면, 기본적으로 다음 패키지들이 필요합니다 (예시):

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy aiomysql \
    mysql-connector-python pandas httpx python-multipart pytz cryptography
```

필요 시 추가로 프로젝트에서 사용하는 다른 모듈도 설치해 주세요.

#### 4-3. MySQL 데이터베이스 준비

1. MySQL 서버를 실행합니다.
2. 아래와 같이 **스키마(데이터베이스)** 를 생성합니다.

```sql
CREATE DATABASE ship_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. 접속 계정/비밀번호를 생성하거나, 기존 계정을 사용합니다.

---

### 5. 민감정보(DB 정보, API 키) 설정 방법

GitHub에는 아래와 같은 정보가 **비워진 값/더미 값**으로 올라갑니다.  
실제 운용 시에는 **환경변수 또는 로컬 전용 설정 파일**로 값을 주입해서 사용해야 합니다.

#### 5-1. `db.py` – DATABASE_URL

`db.py`는 대략 아래와 같은 형태의 설정을 사용합니다.

```python
DATABASE_URL = "mysql+aiomysql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>"
```

GitHub에는 실제 계정/비밀번호/호스트가 들어가지 않도록 되어 있으며,  
로컬이나 서버 환경에서는 다음과 같은 방법 중 하나로 설정하는 것을 권장합니다.

- **환경변수 사용 (권장)**  
  - OS 환경변수에 `DATABASE_URL`을 등록한 뒤, `db.py`에서 `os.getenv("DATABASE_URL")`로 읽어 사용하는 패턴
- **.env 파일 사용**  
  - `.env` 파일을 Git에 올리지 않고 로컬에만 두고, `python-dotenv` 등으로 로드
- **별도 설정 파일**  
  - 예: `config_local.py`를 `.gitignore`에 추가하고 여기에서 실제 URL을 관리

#### 5-2. `data_ingestion.py` – MySQL 접속 설정

`data_ingestion.py`는 CSV 데이터를 MySQL로 적재하기 위해 대략 아래와 비슷한 설정을 사용합니다.

```python
DB_CONFIG = {
    "host": "<HOST>",
    "user": "<USER>",
    "password": "<PASSWORD>",
    "database": "<DB_NAME>",
}
```

GitHub에는 실제 주소/계정/비밀번호가 제거된 상태로 올라가며,  
실행 환경에서 아래와 같이 값을 채워 넣어야 합니다.

- 환경변수에서 읽어와서 `DB_CONFIG`를 구성
- 또는, 로컬 전용 설정 파일에서 import 하도록 변경

이 스크립트는 **테스트/초기 적재용 스크립트**의 성격이 강하므로,  
운영 환경에서는 DB 계정 권한과 네트워크 접근 제어를 충분히 제한하는 것을 권장합니다.

#### 5-3. `services/weather_service.py` – WEATHER_API_KEY

`services/weather_service.py`는 외부 **Weather API(예: WeatherAPI.com)** 를 사용하며,  
코드 상에서 `WEATHER_API_KEY` 상수를 통해 인증 정보를 주입받습니다.

```python
WEATHER_API_KEY = "<YOUR_WEATHER_API_KEY>"
```

GitHub에는 이 값이 비워져 있거나 더미 키만 들어가며,  
다음과 같은 방식으로 실제 키를 설정할 수 있습니다.

- 환경변수 `WEATHER_API_KEY`를 설정하고, 코드에서 `os.getenv("WEATHER_API_KEY")`로 읽기
- `.env` 파일에 `WEATHER_API_KEY=...` 를 명시하고, `python-dotenv`로 로드

>  **주의**  
> - 실제 API 키는 절대로 GitHub에 올리지 마세요.  
> - 키 유출 시, 외부에서 무단 호출이 발생할 수 있으므로,  
>   키가 노출되었다고 의심될 경우 즉시 키를 재발급하거나 폐기해야 합니다.

#### 5-4. 암호화 키(`keys/` 디렉터리)

`services/encryption_utils.py`는 승객 개인정보(예: 생년월일, 연락처, 지병 여부)를 암호화/복호화합니다.  
이때 사용하는 **RSA 키쌍 또는 대칭키**는 일반적으로 `keys/` 디렉터리에 저장하도록 구성합니다.

- `keys/` 디렉터리와 실제 키 파일은 **Git에 올리지 않는 것(.gitignore)** 을 강력 추천합니다.
- 운영 환경에서는 키 파일 권한을 최소화하고,  
  필요 시 키 관리 시스템(KMS) 등을 사용하는 방안을 고려할 수 있습니다.

---

### 6. 애플리케이션 실행 방법

1. (옵션) 가상환경 활성화 및 패키지 설치
2. DB 및 API 키, 암호화 키 등 **민감정보를 모두 설정**했는지 확인
3. FastAPI 서버 실행

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 정상적으로 실행되면 브라우저에서 아래 주소로 접속할 수 있습니다.

- 기본 헬스 체크: `http://localhost:8000/`
- 자동 문서화(Swagger UI): `http://localhost:8000/docs`
- ReDoc 문서: `http://localhost:8000/redoc`

---

### 7. 주요 API 개요

자세한 요청/응답 스키마는 각 `routers/*.py`, `models/schemas.py`를 참고하세요.

- **`/user`**
  - `POST /user/login` – 관리자 로그인, 세션 키 반환
  - `POST /user/register` – 관리자 계정 생성
  - `POST /user/logout` – 세션 키 기반 로그아웃

- **`/ship`**
  - `GET /ship/` – 등록된 선박 목록 조회 (관리자 정보 포함)
  - `POST /ship/register` – 선박 등록

- **`/navigation`**
  - `GET /navigation/routes/{route_id}` – 항로에 대한 GeoJSON 정보
  - `GET /navigation/routes/{route_id}/info` – 거리/예상 소요 시간 등 요약 정보

- **`/weather`**
  - `GET /weather/route/{route_id}` – 항로 기준 현재 날씨 조회
  - `GET /weather/route/{route_id}/forecast?offset={시간}` – 기준 시각 대비 offset 시간 후의 예보 조회

- **`/passenger`**
  - `GET /passenger/{passenger_id}` – 특정 승객 상세 정보(복호화 후) 조회
  - `GET /passenger/?admin_id={id}` – 관리자가 접근 가능한 승객 목록 조회
  - `POST /passenger/upload-csv` – CSV 파일 업로드 후 암호화하여 DB 적재

- **`/logs`**
  - 운항/상황 로그의 생성 및 조회 API (구체 내용은 `routers/logs.py` 참고)

---

### 8. 주의사항 및 권장 사항

- **민감정보는 항상 환경변수 또는 Git에 포함되지 않는 설정 파일로 관리**하세요.
- Weather API와 DB 연결이 끊기면 관련 기능(날씨 조회, 데이터 적재 등)은 **부분적으로 실패**할 수 있습니다.
- 운영 환경에서는
  - CORS 설정을 필요한 도메인만 허용하도록 조정하고,
  - DB 계정 권한 및 네트워크 접근 제어를 최소 권한 원칙에 따라 설정하며,
  - 암호화 키 및 API 키를 안전한 키 관리 체계에서 관리할 것을 권장합니다.


