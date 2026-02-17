# 보안 강화 구현 가이드

> **Rate Limiting, Security Headers, HTTPS 강제 적용**

---

## 구현된 보안 기능

### 1. Rate Limiting (slowapi)

#### 설치

```bash
pip install slowapi redis
```

#### 적용 (`app/main.py`)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.middleware.rate_limit import setup_rate_limiting

# Limiter 설정
setup_rate_limiting(app)
```

#### 엔드포인트별 제한

```python
from app.middleware.rate_limit import limiter

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    pass

@app.post("/api/v1/writer/generate")
@limiter.limit("10/minute")
async def generate_script(request: Request):
    pass
```

---

### 2. Security Headers

#### 적용 (`app/main.py`)

```python
from app.middleware.security_headers import setup_security_headers

# Security Headers 추가
setup_security_headers(app)
```

#### 추가되는 헤더

| 헤더 | 값 | 목적 |
|------|-----|------|
| X-Content-Type-Options | nosniff | MIME 스니핑 방지 |
| X-Frame-Options | DENY | Clickjacking 방지 |
| X-XSS-Protection | 1; mode=block | XSS 방지 |
| Strict-Transport-Security | max-age=31536000 | HTTPS 강제 |
| Content-Security-Policy | default-src 'self' | XSS/데이터 주입 방지 |

---

### 3. HTTPS 강제 (프로덕션)

#### 적용 (`app/main.py`)

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

### 4. CORS 정책 강화

#### 프로덕션 설정

```python
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security_headers import get_allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(debug=settings.DEBUG),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

---

## 배포 전 보안 체크리스트

```python
# app/core/config.py
from app.middleware.security_headers import validate_security_config

# 앱 시작 시 검증
validate_security_config()
```

### 검증 항목

- ✅ SECRET_KEY 32자 이상
- ✅ DEBUG 모드 비활성화 (프로덕션)
- ✅ HTTPS 강제
- ✅ API 키 존재 확인

---

## 프로덕션 배포 명령어

```bash
# 1. 보안 설정 확인
python -c "from app.middleware.security_headers import validate_security_config; validate_security_config()"

# 2. 배포
kamal deploy

# 3. HTTPS 확인
curl -I https://api.omnivibepro.com
```

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
