# 프로덕션 배포 전 체크리스트

> **배포 전 필수 확인 사항 - 순서대로 진행하세요**

---

## ✅ 1. 환경 변수 설정

### .env.production 생성

```bash
cd /Volumes/Extreme\ SSD/02_GitHub.nosync/0030_OmniVibePro/backend
cp .env.example .env.production
```

### 필수 환경 변수 확인

```bash
# 프로덕션 설정
ENV=production
DEBUG=False
SECRET_KEY=<32자 이상 랜덤 문자열>

# 데이터베이스
DATABASE_URL=sqlite:///omni_db.sqlite

# Redis
REDIS_URL=redis://redis:6379/0

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<강력한 비밀번호>

# AI API 키
ELEVENLABS_API_KEY=sk_...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://api.omnivibepro.com/api/v1/auth/google/callback

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Cloudinary
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Monitoring
LOGFIRE_TOKEN=...
SENTRY_DSN=...

# HTTPS
FORCE_HTTPS=True
```

---

## ✅ 2. 보안 검증

### SECRET_KEY 생성 (32자 이상)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 보안 설정 자동 검증

```bash
cd backend
source venv/bin/activate
python -c "from app.middleware.security_headers import validate_security_config; validate_security_config()"
```

**예상 출력**:
```
✓ Security configuration validated
```

---

## ✅ 3. 데이터베이스 최적화

### SQLite WAL 모드 활성화

```bash
cd backend
source venv/bin/activate
python -m app.db.sqlite_optimization
```

**예상 출력**:
```
✓ WAL mode enabled
✓ Synchronous mode set to NORMAL
✓ Cache size set to 64MB
...
✅ Database optimization completed!
```

### 백업 생성

```bash
./scripts/backup_db.sh
```

---

## ✅ 4. 의존성 패키지 설치

### Backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

---

## ✅ 5. 보안 강화 적용

### Rate Limiting + Security Headers

```python
# backend/app/main.py 확인
from app.middleware.rate_limit import setup_rate_limiting
from app.middleware.security_headers import setup_security_headers

setup_rate_limiting(app)
setup_security_headers(app)
```

### requirements.txt에 slowapi 추가

```bash
echo "slowapi>=0.1.9" >> requirements.txt
pip install slowapi
```

---

## ✅ 6. 테스트 실행

### Unit 테스트

```bash
cd backend
pytest tests/unit/ -v
```

### API 헬스 체크

```bash
# 개발 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 헬스 체크
curl http://localhost:8000/health

# 예상 응답:
# {"status":"online","version":"1.0.0"}
```

---

## ✅ 7. Docker 이미지 준비

### Dockerfile 확인

```bash
# backend/Dockerfile 존재 확인
ls -la backend/Dockerfile

# frontend/Dockerfile 존재 확인
ls -la frontend/Dockerfile
```

---

## ✅ 8. 프로덕션 설정 파일 확인

### 체크리스트

- [ ] `.env.production` 생성 및 모든 변수 설정
- [ ] `DEBUG=False` 확인
- [ ] `FORCE_HTTPS=True` 확인
- [ ] `SECRET_KEY` 32자 이상
- [ ] 모든 API 키 실제 값 입력
- [ ] SQLite WAL 모드 활성화
- [ ] 데이터베이스 백업 완료
- [ ] `slowapi` 설치
- [ ] 테스트 통과
- [ ] Dockerfile 존재
- [ ] `.gitignore`에 `.env*` 포함

---

## ✅ 9. Git 커밋 (배포 전)

```bash
git add .
git commit -m "chore: production deployment preparation

- Add rate limiting middleware
- Add security headers middleware
- Optimize SQLite for production
- Add deployment configurations
- Complete security hardening (A+ grade)
"
git push origin main
```

---

## ✅ 10. 최종 확인

### 환경 변수 출력 (민감 정보 제외)

```bash
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'ENV: {settings.ENV}')
print(f'DEBUG: {settings.DEBUG}')
print(f'FORCE_HTTPS: {getattr(settings, \"FORCE_HTTPS\", False)}')
print(f'SECRET_KEY length: {len(settings.SECRET_KEY)}')
print(f'ELEVENLABS_API_KEY: {\"SET\" if settings.ELEVENLABS_API_KEY else \"NOT SET\"}')
print(f'OPENAI_API_KEY: {\"SET\" if settings.OPENAI_API_KEY else \"NOT SET\"}')
print(f'STRIPE_SECRET_KEY: {\"SET\" if settings.STRIPE_SECRET_KEY else \"NOT SET\"}')
"
```

**예상 출력**:
```
ENV: production
DEBUG: False
FORCE_HTTPS: True
SECRET_KEY length: 43
ELEVENLABS_API_KEY: SET
OPENAI_API_KEY: SET
STRIPE_SECRET_KEY: SET
```

---

## 🚀 준비 완료!

모든 체크리스트 ✅가 완료되면 다음 단계로 진행:

**→ Task #32: Docker 이미지 빌드 및 푸시**

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
