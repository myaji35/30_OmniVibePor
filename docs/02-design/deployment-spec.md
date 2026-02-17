# OmniVibe Pro - 배포 명세서 (Phase 9)

**작성일**: 2026-02-17
**레벨**: Enterprise
**배포 환경**: Vultr VPS + Docker Compose + Nginx

---

## 아키텍처 다이어그램

```
인터넷
  │
  ▼
[Nginx :80/:443]
  ├── omnivibepro.com → frontend:3020
  ├── api.omnivibepro.com → backend:8000
  └── /ws/* → backend:8000 (WebSocket)
       │
       ├── [Frontend - Next.js :3020]  ← standalone 빌드
       ├── [Backend - FastAPI :8000]   ← uvicorn 4 workers
       ├── [Celery Worker]             ← 동시 4개
       ├── [Celery Beat]               ← 스케줄러
       ├── [Redis :6379]               ← 메시지 브로커 + 캐시
       └── [Neo4j :7474/:7687]         ← GraphRAG
```

---

## 서비스 포트 매핑

| 서비스 | 내부 포트 | 외부 노출 | 비고 |
|-------|---------|---------|------|
| Frontend (Next.js) | 3020 | 3020 (nginx 경유) | standalone 빌드 |
| Backend (FastAPI) | 8000 | 8000 (nginx 경유) | uvicorn 4 workers |
| Redis | 6379 | 비노출 | 내부 전용 |
| Neo4j HTTP | 7474 | 7474 | 관리 목적만 |
| Neo4j Bolt | 7687 | 7687 | 내부 전용 권장 |
| Nginx HTTP | 80 | 80 | HTTPS 리다이렉트 |
| Nginx HTTPS | 443 | 443 | SSL 터미네이션 |

---

## 필수 환경변수 체크리스트

### Backend (.env 또는 docker-compose 환경변수)

```bash
# 필수 (미설정 시 서버 시작 불가)
SECRET_KEY=                    # JWT 서명 키 (최소 32자 랜덤 문자열)
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=                # 강력한 패스워드
OPENAI_API_KEY=                # GPT-4 + Whisper
ANTHROPIC_API_KEY=             # Claude
ELEVENLABS_API_KEY=            # TTS
GOOGLE_VEO_API_KEY=            # Video generation
GOOGLE_SHEETS_CREDENTIALS_PATH=
YOUTUBE_API_KEY=
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
LOGFIRE_TOKEN=                 # Observability (optional)

# 프로덕션 필수 추가
FRONTEND_URL=https://omnivibepro.com
CORS_ORIGINS=https://omnivibepro.com,https://www.omnivibepro.com
DEBUG=false

# 선택 (기능 활성화 시)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### Frontend (docker-compose 환경변수)
```bash
NEXT_PUBLIC_API_URL=https://api.omnivibepro.com
PORT=3020
HOSTNAME=0.0.0.0
```

---

## 배포 전 체크리스트

### 코드 준비
- [x] Backend API 전체 구현 (28개 라우터, 120+ 엔드포인트)
- [x] Frontend UI 구현 (14개 페이지, 42개 컴포넌트)
- [x] SLDS 디자인 시스템 적용
- [x] Next.js 프록시 API (직접 호출 제거)
- [x] TypeScript 빌드 오류 수정
- [x] CORS 와일드카드 제거 → 환경변수 기반
- [x] 하드코딩 URL 제거 (billing.py)
- [x] Python 문법 오류 수정 (audio_correction_loop, content_performance_tracker)

### 인프라 준비
- [x] Docker Compose (prod) 구성
- [x] Nginx reverse proxy 설정 (포트 통일: 3020)
- [x] SSL 인증서 디렉토리 (`nginx/ssl/`)
- [x] Next.js standalone 빌드 설정 (`output: 'standalone'`)
- [x] Dockerfile.production (frontend 포트 3020 통일)
- [ ] SSL 인증서 발급 (Let's Encrypt)
- [ ] 도메인 DNS 설정
- [ ] Vultr VPS 접근 권한 확인

### 보안
- [x] JWT 인증 구현
- [x] Rate Limiting (Nginx + FastAPI 이중)
- [x] Security Headers (middleware + Nginx)
- [x] CORS 도메인 화이트리스트
- [ ] 환경변수 `.env` 파일 서버에 복사 (`.gitignore` 확인)
- [ ] Neo4j 기본 패스워드 변경 확인

---

## 배포 명령어

```bash
# 1. 서버 접속
ssh root@{VULTR_IP}

# 2. 프로젝트 클론
git clone <repo_url> /opt/omnivibepro
cd /opt/omnivibepro

# 3. 환경변수 설정
cp .env.example .env
nano .env  # 실제 값 입력

# 4. SSL 인증서 발급
apt install certbot
certbot certonly --standalone -d omnivibepro.com -d www.omnivibepro.com -d api.omnivibepro.com
cp /etc/letsencrypt/live/omnivibepro.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/omnivibepro.com/privkey.pem nginx/ssl/

# 5. 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d --build

# 6. 헬스 체크
curl http://localhost:8000/health
curl http://localhost:3020

# 7. 로그 확인
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

---

## 롤백 계획

```bash
# 이전 이미지로 즉시 롤백
docker-compose -f docker-compose.prod.yml down
git checkout {이전_커밋_해시}
docker-compose -f docker-compose.prod.yml up -d --build

# 데이터베이스 백업 복구 (SQLite)
cp backend/backups/omni_db_{날짜}.sqlite backend/omni_db.sqlite
docker-compose -f docker-compose.prod.yml restart backend
```

---

## 모니터링

| 항목 | 방법 | 경로 |
|------|------|------|
| Backend 헬스 | HTTP GET | `https://api.omnivibepro.com/health` |
| API 문서 | Swagger UI | `https://api.omnivibepro.com/docs` |
| Celery 태스크 | Flower | `http://{SERVER_IP}:5555` |
| Neo4j | Browser | `http://{SERVER_IP}:7474` |
| 로그 | Docker logs | `docker-compose logs -f` |
