# 🔐 보안 정보 (암호화 보관 필수!)

> **⚠️ 이 파일은 절대 Git에 커밋하지 마세요!**
> **⚠️ .gitignore에 추가되어 있습니다**

---

## Vultr 서버 정보

### 서버 접속
```
IP: 158.247.235.31
User: root
Password: B6n!o]U@[5P}tL)H
```

### SSH 접속 명령어
```bash
ssh root@158.247.235.31
```

---

## 환경 변수 (.env)

### 프로덕션 환경 변수
```bash
ENV=production
DEBUG=False
SECRET_KEY=<자동 생성됨>

# Database
DATABASE_URL=sqlite:///omni_db.sqlite
REDIS_URL=redis://redis:6379/0

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_prod_password_2026

# AI API Keys (실제 값으로 교체 필요)
ELEVENLABS_API_KEY=sk_...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Stripe (실제 값으로 교체 필요)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Cloudinary (실제 값으로 교체 필요)
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Google OAuth (실제 값으로 교체 필요)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://api.omnivibepro.com/api/v1/auth/google/callback

# Monitoring
LOGFIRE_TOKEN=...

# Security
FORCE_HTTPS=True (도메인 설정 후)
```

---

## 배포 기록

### 최초 배포
- **날짜**: 2026-02-08
- **서버**: Vultr (158.247.235.31)
- **플랫폼**: Docker Compose
- **OS**: Ubuntu 22.04

### 배포 명령어
```bash
cd "/Volumes/Extreme SSD/02_GitHub.nosync/0030_OmniVibePro"
./scripts/auto_deploy.sh
```

---

## 보안 체크리스트

- [x] .gitignore에 .env 추가
- [x] .gitignore에 credentials 파일 추가
- [ ] SSH 키 기반 인증 설정
- [ ] root 비밀번호 변경
- [ ] deploy 사용자 생성
- [ ] 방화벽 설정 (UFW)
- [ ] Fail2ban 설치
- [ ] 자동 백업 설정

---

## 긴급 연락처

**서버 문제 시**:
- Vultr Support: https://my.vultr.com/support/
- Discord: (추가 예정)

---

## 백업 위치

- **서버**: /root/omnivibe/backups/
- **로컬**: /Volumes/Extreme SSD/backups/

---

**⚠️ 이 파일을 안전한 곳에 보관하세요!**
**⚠️ 1Password, LastPass 등 비밀번호 관리자 사용 권장**

**마지막 업데이트**: 2026-02-08
