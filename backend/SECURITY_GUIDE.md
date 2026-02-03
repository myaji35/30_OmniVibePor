# OmniVibe Pro - Security Guide

## Overview

OmniVibe Pro는 다층 보안 아키텍처를 사용하여 사용자 데이터와 API를 보호합니다. 이 가이드는 구현된 보안 기능과 사용 방법을 설명합니다.

---

## 📋 Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Rate Limiting](#rate-limiting)
3. [Security Headers](#security-headers)
4. [Input Validation & Sanitization](#input-validation--sanitization)
5. [Audit Logging](#audit-logging)
6. [API Key Management](#api-key-management)
7. [Best Practices](#best-practices)
8. [Security Checklist](#security-checklist)

---

## 🔐 Authentication & Authorization

### JWT Authentication

OmniVibe Pro는 JWT (JSON Web Token) 기반 인증을 사용합니다.

#### Token Types

1. **Access Token**: 30분 유효, API 요청 인증용
2. **Refresh Token**: 7일 유효, Access Token 갱신용

#### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Redis
    participant Neo4j

    Client->>API: POST /auth/login (email, password)
    API->>Neo4j: Verify credentials
    Neo4j-->>API: User data
    API->>Redis: Store session (optional)
    API-->>Client: Access Token + Refresh Token

    Client->>API: GET /api/v1/audio/generate (Bearer Token)
    API->>Redis: Check blacklist
    API->>API: Verify JWT signature
    API->>Neo4j: Get user data
    API-->>Client: Response with data
```

#### Usage Example

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

**Authenticated Request:**
```bash
curl -X POST http://localhost:8000/api/v1/audio/generate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"script": "Hello World", "voice_id": "voice_123"}'
```

### User Roles

OmniVibe Pro는 다음 역할을 지원합니다:

- **admin**: 모든 권한 (사용자 관리, 통계 조회 등)
- **user**: 일반 사용자 (자신의 리소스 생성/관리)
- **viewer**: 읽기 전용 (조회만 가능)

#### Role-Based Access Control (RBAC)

```python
from fastapi import Depends
from app.auth.dependencies import require_role
from app.models.user import UserRole

@router.get("/admin/users", dependencies=[Depends(require_role([UserRole.ADMIN]))])
async def list_all_users():
    # Admin만 접근 가능
    pass
```

### Password Requirements

- 최소 8자 이상
- 대문자 1개 이상
- 소문자 1개 이상
- 숫자 1개 이상

---

## 🚦 Rate Limiting

Rate Limiting은 API 남용을 방지하고 서비스 안정성을 보장합니다.

### Rate Limit Tiers

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/audio/generate` | 10 requests | 1 hour |
| `/api/v1/presentations/generate-video` | 5 requests | 1 hour |
| `/api/v1/voice/clone` | 5 requests | 1 hour |
| **Default** | 1000 requests | 1 hour |

### Rate Limit Headers

모든 응답에 다음 헤더가 포함됩니다:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 3456
```

- `X-RateLimit-Limit`: 시간 윈도우당 최대 요청 수
- `X-RateLimit-Remaining`: 남은 요청 수
- `X-RateLimit-Reset`: 리셋까지 남은 시간 (초)

### Rate Limit Exceeded

```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per 1 hour(s)."
}
```

**HTTP Status**: 429 Too Many Requests

### Per-User vs Per-IP

- **인증된 사용자**: `user_id` 기반 Rate Limit
- **비인증 사용자**: IP 주소 기반 Rate Limit

---

## 🛡️ Security Headers

OmniVibe Pro는 OWASP 권장 보안 헤더를 자동으로 추가합니다.

### Implemented Headers

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()...
```

### Header Descriptions

- **CSP (Content Security Policy)**: XSS 공격 방지
- **X-Frame-Options**: 클릭재킹 방지
- **X-Content-Type-Options**: MIME 스니핑 방지
- **X-XSS-Protection**: 레거시 XSS 필터 활성화
- **HSTS**: HTTPS 강제 (프로덕션 환경)
- **Referrer-Policy**: 리퍼러 정보 제어
- **Permissions-Policy**: 브라우저 기능 접근 제어

---

## ✅ Input Validation & Sanitization

모든 사용자 입력은 검증 및 정제됩니다.

### XSS Prevention

```python
from app.validators import sanitize_text

# Before
user_input = "<script>alert('XSS')</script>"

# After
safe_input = sanitize_text(user_input)
# Result: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
```

### File Upload Validation

```python
from app.validators import validate_file_upload

@router.post("/upload")
async def upload_file(file: UploadFile):
    # 파일 타입, 크기, 이름 검증
    await validate_file_upload(file, file_category="image")

    # 안전한 파일명 생성
    safe_filename = sanitize_filename(file.filename)

    # 파일 저장
    ...
```

### Allowed File Types

| Category | Allowed Types | Max Size |
|----------|---------------|----------|
| **Image** | JPEG, PNG, GIF, WebP | 10MB |
| **Audio** | MP3, WAV, OGG, FLAC | 50MB |
| **Video** | MP4, MPEG, MOV, WebM | 500MB |
| **Document** | PDF, PPT, PPTX | 20MB |

### Path Traversal Prevention

```python
from app.validators import prevent_path_traversal

# Dangerous
filename = "../../etc/passwd"
safe = prevent_path_traversal(filename)
# Result: None (blocked)

# Safe
filename = "document.pdf"
safe = prevent_path_traversal(filename)
# Result: "document.pdf"
```

---

## 📊 Audit Logging

모든 인증 및 리소스 접근 이벤트는 Neo4j에 기록됩니다.

### Logged Events

#### Authentication Events
- `register_success` / `register_failed`
- `login_success` / `login_failed`
- `logout`
- `password_change_success` / `password_change_failed`
- `api_key_created` / `api_key_revoked`

#### Resource Events
- `project_created` / `project_deleted`
- `audio_generated`
- `video_rendered`
- `file_uploaded` / `file_deleted`

#### Security Events
- `rate_limit_exceeded`
- `invalid_token`
- `unauthorized_access`
- `file_validation_failed`

### Usage Example

```python
from app.services.audit_logger import log_auth_event, log_resource_event

# 인증 이벤트 로깅
await log_auth_event(
    event_type="login_success",
    user_id="user_abc123",
    email="user@example.com",
    ip_address="192.168.1.1"
)

# 리소스 이벤트 로깅
await log_resource_event(
    event_type="project_created",
    user_id="user_abc123",
    resource_type="project",
    resource_id="proj_xyz789",
    action="create",
    status="success"
)
```

### Querying Audit Logs

```python
from app.services.audit_logger import get_user_audit_logs

# 사용자의 최근 100개 로그 조회
logs = await get_user_audit_logs(
    user_id="user_abc123",
    limit=100
)

# 특정 이벤트 타입 필터
logs = await get_user_audit_logs(
    user_id="user_abc123",
    event_type="login_success"
)
```

### Admin: Security Events

```python
from app.services.audit_logger import get_security_events
from datetime import datetime, timedelta

# 최근 7일간 보안 이벤트 조회
start_date = datetime.utcnow() - timedelta(days=7)
events = await get_security_events(
    start_date=start_date,
    limit=100
)
```

---

## 🔑 API Key Management

JWT 토큰 외에 API 키를 사용한 인증도 지원합니다.

### Creating API Keys

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "expires_in_days": 365,
    "rate_limit": 5000
  }'
```

**Response:**
```json
{
  "key_id": "key_abc123",
  "name": "Production API Key",
  "api_key": "ovp_8xK3p9mN2vL5qW7rT4uY1sZ0aH6bC9dE",
  "prefix": "ovp_8xK3p9mN",
  "created_at": "2026-02-02T12:00:00Z",
  "expires_at": "2027-02-02T12:00:00Z",
  "rate_limit": 5000
}
```

⚠️ **중요**: API 키는 생성 시 1회만 표시됩니다. 안전한 곳에 보관하세요.

### Using API Keys

```bash
curl -X POST http://localhost:8000/api/v1/audio/generate \
  -H "X-API-Key: ovp_8xK3p9mN2vL5qW7rT4uY1sZ0aH6bC9dE" \
  -H "Content-Type: application/json" \
  -d '{"script": "Hello World", "voice_id": "voice_123"}'
```

### API Key Best Practices

1. **환경 변수 사용**: 코드에 직접 하드코딩하지 마세요
   ```bash
   export OMNIVIBE_API_KEY="ovp_8xK3p9mN..."
   ```

2. **최소 권한 원칙**: 필요한 권한만 부여
3. **정기적 교체**: 90일마다 API 키 재발급
4. **모니터링**: API 키 사용량 추적
5. **즉시 폐기**: 유출 의심 시 즉시 비활성화

### Revoking API Keys

```bash
curl -X DELETE http://localhost:8000/api/v1/auth/api-keys/key_abc123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔒 Best Practices

### 1. Environment Variables

**절대 하지 말아야 할 것:**
```python
# ❌ Bad
SECRET_KEY = "my-secret-key-123"
```

**권장 방법:**
```python
# ✅ Good
from app.core.config import get_settings
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
```

### 2. Password Storage

- ✅ Bcrypt 해싱 사용
- ❌ 평문 저장 금지
- ❌ MD5/SHA1 사용 금지

### 3. HTTPS Only (Production)

```nginx
# Nginx configuration
server {
    listen 80;
    server_name omnivibepro.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name omnivibepro.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 4. CORS Configuration

**개발 환경:**
```python
allow_origins=["*"]  # 모든 도메인 허용
```

**프로덕션 환경:**
```python
allow_origins=[
    "https://omnivibepro.com",
    "https://app.omnivibepro.com",
]
```

### 5. Database Security

- ✅ 파라미터화된 쿼리 사용
- ❌ 문자열 결합 쿼리 금지
- ✅ 최소 권한 DB 사용자

### 6. Secrets Management

```bash
# .env 파일 권한 설정
chmod 600 .env

# Git에서 제외
echo ".env" >> .gitignore
```

### 7. Dependency Updates

```bash
# 정기적인 보안 업데이트
poetry update
poetry audit  # 취약점 스캔
```

---

## ✔️ Security Checklist

### Deployment Checklist

- [ ] `DEBUG = False` 설정
- [ ] `SECRET_KEY` 충분히 복잡한 랜덤 키 사용 (최소 64자)
- [ ] HTTPS 활성화 (SSL/TLS 인증서)
- [ ] CORS 도메인 화이트리스트 설정
- [ ] Rate Limiting 활성화 확인
- [ ] 모든 환경 변수 설정 확인
- [ ] `.env` 파일 권한 확인 (`chmod 600`)
- [ ] Redis 비밀번호 설정
- [ ] Neo4j 비밀번호 강력하게 설정
- [ ] Firewall 규칙 설정 (필요한 포트만 개방)
- [ ] 로그 모니터링 설정
- [ ] 백업 자동화 설정
- [ ] DDoS 방어 설정
- [ ] API 키 로테이션 정책 수립

### Code Review Checklist

- [ ] 모든 엔드포인트에 인증 적용
- [ ] 민감한 데이터 로그에 노출 방지
- [ ] SQL/Cypher Injection 방어 확인
- [ ] XSS 방어 확인
- [ ] CSRF 방어 확인 (해당하는 경우)
- [ ] 파일 업로드 검증 확인
- [ ] Rate Limiting 적용 확인
- [ ] 에러 메시지에 민감 정보 노출 방지
- [ ] 의존성 취약점 스캔
- [ ] 타입 힌트 사용 (타입 안정성)

### Testing Checklist

- [ ] 인증 테스트 (유효/만료/위조 토큰)
- [ ] 권한 테스트 (RBAC)
- [ ] Rate Limiting 테스트
- [ ] 입력 검증 테스트 (XSS, SQLi, Path Traversal)
- [ ] 파일 업로드 테스트 (악성 파일, 크기 초과)
- [ ] API 키 테스트 (유효/만료/폐기)
- [ ] 감사 로그 테스트
- [ ] 보안 헤더 테스트
- [ ] 암호화 테스트
- [ ] 세션 관리 테스트

---

## 🆘 Incident Response

### Security Incident Detected

1. **즉시 조치**:
   - 영향받는 API 키/토큰 즉시 폐기
   - 의심스러운 IP 차단
   - 로그 백업 및 보존

2. **조사**:
   ```python
   # 의심스러운 활동 조회
   events = await get_security_events(
       event_type="unauthorized_access",
       start_date=datetime.utcnow() - timedelta(hours=24)
   )
   ```

3. **복구**:
   - 취약점 패치
   - 영향받은 사용자 통보
   - 비밀번호 재설정 요청

4. **사후 분석**:
   - 근본 원인 분석
   - 재발 방지 대책 수립
   - 문서화

### Emergency Contacts

- **보안 팀**: security@omnivibepro.com
- **기술 지원**: support@omnivibepro.com
- **관리자**: admin@omnivibepro.com

---

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Redis Security](https://redis.io/topics/security)
- [Neo4j Security](https://neo4j.com/docs/operations-manual/current/security/)

---

## 📝 Version History

- **v1.0.0** (2026-02-02): Initial security implementation
  - JWT authentication
  - Rate limiting
  - Security headers
  - Input validation
  - Audit logging
  - API key management

---

## 📞 Support

보안 관련 질문이나 취약점 발견 시:
- 이메일: security@omnivibepro.com
- GitHub: [Security Advisory](https://github.com/omnivibe-pro/issues)

**책임 있는 공개 정책**: 취약점을 발견하셨다면 공개하기 전에 먼저 보안 팀에 연락해 주세요.
