# Security Guide - OmniVibe Pro

> **프로덕션 환경 보안 설정 가이드**

---

## 📋 목차

1. [환경 변수 보안](#환경-변수-보안)
2. [Rate Limiting](#rate-limiting)
3. [API Key 인증](#api-key-인증)
4. [CORS 정책](#cors-정책)
5. [HTTPS 설정](#https-설정)
6. [보안 헤더](#보안-헤더)
7. [비밀번호 정책](#비밀번호-정책)

---

## 환경 변수 보안

### 1. Secrets 생성

```bash
# SECRET_KEY 생성 (32바이트 hex)
openssl rand -hex 32

# 강력한 비밀번호 생성
openssl rand -base64 32
```

### 2. .env.production 설정

```bash
cp .env.production.template .env.production
nano .env.production
```

**중요**: `.env.production`은 절대 Git에 커밋하지 마세요!

```.gitignore
# .gitignore
.env.production
*.env.production
secrets/
credentials/
```

### 3. Docker Secrets 사용 (권장)

```bash
# Docker secret 생성
echo "your_secret_value" | docker secret create elevenlabs_key -

# docker-compose.yml에서 사용
services:
  backend:
    secrets:
      - elevenlabs_key
```

---

## Rate Limiting

### 설정

```python
# app/main.py
from app.middleware.security import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    calls=60,  # 60 requests
    period=60  # per 60 seconds
)
```

### 응답 헤더

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1707123456
```

### 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Max 60 requests per 60 seconds.",
  "retry_after": 30
}
```

---

## API Key 인증

### 1. API Key 생성

```python
import hashlib
import secrets

# API Key 생성
api_key = secrets.token_urlsafe(32)
print(f"API Key: {api_key}")

# Hash 저장 (DB에 저장할 값)
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
print(f"Hash: {api_key_hash}")
```

### 2. 미들웨어 적용

```python
# app/main.py
from app.middleware.security import APIKeyMiddleware

# 프로덕션에서만 활성화
if not settings.DEBUG:
    app.add_middleware(
        APIKeyMiddleware,
        api_key_header="X-API-Key"
    )
```

### 3. API 호출

```bash
curl -H "X-API-Key: your_api_key_here" \
  https://api.omnivibepro.com/api/v1/writer/generate
```

### 4. 인증 실패

```json
{
  "error": "Missing API Key",
  "detail": "API Key required in 'X-API-Key' header"
}
```

---

## CORS 정책

### 프로덕션 설정

```python
from fastapi.middleware.cors import CORSMiddleware

# 허용된 도메인만
allowed_origins = [
    "https://omnivibepro.com",
    "https://studio.omnivibepro.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 특정 도메인만
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

### 개발 환경

```python
# 개발 환경에서만 모든 도메인 허용
if settings.DEBUG:
    allowed_origins = ["*"]
```

---

## HTTPS 설정

### 1. Let's Encrypt SSL 인증서

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d omnivibepro.com -d www.omnivibepro.com
```

### 2. Nginx HTTPS 리다이렉트

```nginx
# /etc/nginx/sites-available/omnivibe
server {
    listen 80;
    server_name omnivibepro.com;
    
    # HTTP → HTTPS 리다이렉트
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name omnivibepro.com;
    
    ssl_certificate /etc/letsencrypt/live/omnivibepro.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/omnivibepro.com/privkey.pem;
    
    # SSL 설정 (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://backend:8000;
    }
}
```

### 3. 자동 갱신

```bash
# Cron job 추가
sudo crontab -e

# 매일 2시에 인증서 갱신 시도
0 2 * * * certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

---

## 보안 헤더

### SecurityHeadersMiddleware

```python
# app/middleware/security.py
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
```

### 헤더 설명

| 헤더 | 설명 |
|------|------|
| X-Content-Type-Options | MIME 타입 스니핑 방지 |
| X-Frame-Options | Clickjacking 방지 |
| X-XSS-Protection | XSS 공격 방지 |
| Strict-Transport-Security | HTTPS 강제 |
| Content-Security-Policy | XSS, 데이터 인젝션 방지 |

---

## 비밀번호 정책

### 1. 비밀번호 해싱

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 해싱
hashed = pwd_context.hash("user_password")

# 검증
is_valid = pwd_context.verify("user_password", hashed)
```

### 2. 비밀번호 요구사항

- 최소 12자
- 대소문자 혼합
- 숫자 포함
- 특수문자 포함

```python
import re

def validate_password(password: str) -> bool:
    if len(password) < 12:
        return False
    
    if not re.search(r"[a-z]", password):
        return False
    
    if not re.search(r"[A-Z]", password):
        return False
    
    if not re.search(r"\d", password):
        return False
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    
    return True
```

---

## 보안 체크리스트

### 배포 전 필수 확인

- [ ] DEBUG=false 설정
- [ ] SECRET_KEY 변경 (랜덤 생성)
- [ ] 모든 API 키 환경 변수로 관리
- [ ] CORS 특정 도메인만 허용
- [ ] Rate Limiting 활성화
- [ ] HTTPS 설정
- [ ] 보안 헤더 적용
- [ ] API Key 인증 활성화
- [ ] .env.production Git 제외
- [ ] 데이터베이스 백업 자동화

### 정기 점검

- [ ] SSL 인증서 유효기간 (90일마다)
- [ ] 의존성 보안 업데이트
- [ ] 접근 로그 검토
- [ ] API Key 로테이션 (6개월마다)
- [ ] 비밀번호 정책 준수

---

## 침해 대응

### 1. API Key 유출 시

```bash
# 1. 즉시 해당 Key 무효화
# 2. 새 Key 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 환경 변수 업데이트
# 4. 서비스 재시작
```

### 2. 의심스러운 활동 감지

```bash
# 접근 로그 확인
tail -f /var/log/nginx/access.log | grep "429\|403\|401"

# 특정 IP 차단
sudo ufw deny from <IP_ADDRESS>
```

---

**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro Security Team
