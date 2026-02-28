# OmniVibe Pro 프로덕션 배포 가이드

> **Kamal + Docker를 활용한 안전한 프로덕션 배포**

---

## 📋 배포 방식 선택

| 방식 | 난이도 | 비용 | 확장성 | 권장 |
|------|--------|------|--------|------|
| **Kamal** | 중 | 낮음 | 중 | ⭐⭐⭐⭐⭐ |
| **Docker Compose** | 낮음 | 낮음 | 낮음 | ⭐⭐⭐⭐ |
| **Kubernetes** | 높음 | 높음 | 높음 | ⭐⭐ (초기X) |
| **Heroku/Render** | 낮음 | 높음 | 중 | ⭐⭐⭐ |

**권장**: Kamal (Zero-downtime deployment)

---

## Kamal 배포 (권장)

### 1. 사전 준비

#### 서버 요구사항

| 리소스 | 최소 | 권장 |
|--------|------|------|
| **RAM** | 4GB | 8GB |
| **CPU** | 2 Core | 4 Core |
| **Storage** | 50GB | 100GB SSD |
| **OS** | Ubuntu 22.04 | Ubuntu 22.04 |

#### 로컬 설치

```bash
# Kamal 설치
gem install kamal

# 버전 확인
kamal version
```

### 2. 서버 설정

#### SSH 접속 설정

```bash
# SSH 키 생성 (로컬)
ssh-keygen -t ed25519 -C "deploy@omnivibepro.com"

# 서버에 키 추가
ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@192.168.1.100
```

#### Docker 설치 (서버)

```bash
# 서버에 SSH 접속
ssh deploy@192.168.1.100

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자 권한 추가
sudo usermod -aG docker $USER
```

### 3. Kamal 설정

#### config/deploy.yml 수정

```yaml
# backend/config/deploy.yml
service: omnivibe-pro
image: omnivibepro/backend

servers:
  web:
    hosts:
      - 123.456.789.012  # 실제 서버 IP
    labels:
      traefik.http.routers.omnivibe.rule: Host(`api.omnivibepro.com`)

registry:
  username: your-dockerhub-username
  password:
    - KAMAL_REGISTRY_PASSWORD

env:
  secret:
    - SECRET_KEY
    - ELEVENLABS_API_KEY
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - STRIPE_SECRET_KEY
```

#### .kamal/secrets 생성

```bash
# .kamal/secrets (절대 Git 커밋 금지)
KAMAL_REGISTRY_PASSWORD=your_dockerhub_password
SECRET_KEY=your_secret_key_min_32_chars
ELEVENLABS_API_KEY=sk_...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEO4J_PASSWORD=your_neo4j_password
```

### 4. 배포 실행

#### 초기 배포

```bash
cd backend

# 1. 설정 확인
kamal config

# 2. 서버 준비 (Docker 등 설치)
kamal server bootstrap

# 3. Accessories 배포 (Redis, Neo4j)
kamal accessory boot redis
kamal accessory boot neo4j

# 4. 앱 배포
kamal setup

# 5. 배포 확인
kamal app logs
```

#### 업데이트 배포

```bash
# Git 커밋 후
git add .
git commit -m "Update: feature X"
git push

# Kamal 배포 (Zero-downtime)
kamal deploy

# 로그 확인
kamal app logs -f
```

### 5. HTTPS 설정 (Let's Encrypt)

```bash
# Traefik 자동 HTTPS
# config/deploy.yml에 이미 설정됨

# 인증서 확인
curl -I https://api.omnivibepro.com
# HTTP/2 200
# strict-transport-security: max-age=31536000
```

---

## Docker Compose 배포 (간단한 방법)

### 1. 서버에 파일 복사

```bash
# 로컬에서
rsync -avz --exclude 'node_modules' --exclude '.next' \
  ./ deploy@192.168.1.100:/var/www/omnivibe/
```

### 2. 환경 변수 설정

```bash
# 서버에서
cd /var/www/omnivibe
cp .env.example .env
nano .env

# .env 파일 편집
SECRET_KEY=...
ELEVENLABS_API_KEY=...
...
```

### 3. Docker Compose 실행

```bash
# 프로덕션 모드로 실행
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f backend

# 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### 4. 업데이트

```bash
# Git Pull
git pull origin main

# 재배포
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 도메인 설정

### 1. DNS 설정

```
# A Record
api.omnivibepro.com    → 123.456.789.012
studio.omnivibepro.com → 123.456.789.012
omnivibepro.com        → 123.456.789.012
```

### 2. Cloudflare 설정 (선택사항)

- **Proxy**: Enabled (오렌지 구름)
- **SSL/TLS**: Full (strict)
- **Always Use HTTPS**: On
- **Auto Minify**: CSS, JS, HTML

---

## 모니터링 설정

### 1. Logfire 연동

```python
# backend/app/main.py
import logfire

logfire.configure(token=settings.LOGFIRE_TOKEN)
logfire.instrument_fastapi(app)
```

**대시보드**: https://logfire.pydantic.dev

### 2. Sentry 연동

```bash
# 설치
pip install sentry-sdk

# 설정
import sentry_sdk

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)
```

**대시보드**: https://sentry.io

### 3. Uptime 모니터링

**서비스**:
- [UptimeRobot](https://uptimerobot.com) (무료)
- [Pingdom](https://pingdom.com)

**설정**:
- URL: `https://api.omnivibepro.com/health`
- Interval: 5분
- Alert: Email, Slack

---

## 백업 자동화

### 1. Cron 백업 스크립트

```bash
# 서버에서
crontab -e

# 매일 새벽 2시 백업
0 2 * * * /var/www/omnivibe/backend/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### 2. S3 원격 백업 (선택사항)

```bash
# AWS CLI 설치
sudo apt install awscli

# 설정
aws configure

# 백업 스크립트 수정
# scripts/backup_db.sh 마지막에 추가
aws s3 cp backups/backup_*.sqlite.gz s3://omnivibe-backups/
```

---

## 성능 최적화

### 1. Nginx 캐싱

```nginx
# nginx/nginx.conf
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /api/v1/campaigns {
    proxy_cache my_cache;
    proxy_cache_valid 200 5m;
}
```

### 2. SQLite WAL 모드

```bash
# 서버에서
cd /var/www/omnivibe/backend
python -m app.db.sqlite_optimization
```

### 3. Redis 메모리 설정

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

## 보안 체크리스트

### 배포 전 필수 확인

- [ ] `DEBUG=False` (프로덕션)
- [ ] `SECRET_KEY` 32자 이상
- [ ] `.env` 파일 `.gitignore`에 포함
- [ ] HTTPS 강제
- [ ] CORS 화이트리스트 설정
- [ ] Rate Limiting 활성화
- [ ] Security Headers 적용
- [ ] 방화벽 설정 (ufw)

### 방화벽 설정

```bash
# UFW 설치
sudo apt install ufw

# 기본 정책 (모두 거부)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH, HTTP, HTTPS 허용
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 활성화
sudo ufw enable
```

---

## 트러블슈팅

### 1. 컨테이너 재시작

```bash
# Kamal
kamal app restart

# Docker Compose
docker-compose -f docker-compose.prod.yml restart backend
```

### 2. 로그 확인

```bash
# Kamal
kamal app logs -f

# Docker Compose
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 3. 데이터베이스 복구

```bash
# 백업에서 복구
cp backups/omni_db_backup_20260208_020000.sqlite omni_db.sqlite

# WAL 파일 적용
sqlite3 omni_db.sqlite "PRAGMA wal_checkpoint(FULL)"
```

### 4. 성능 문제

```bash
# 컨테이너 리소스 사용량
docker stats

# 프로세스 확인
htop

# 디스크 사용량
df -h
```

---

## CI/CD (GitHub Actions)

### .github/workflows/deploy.yml

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Ruby
      uses: ruby/setup-ruby@v1
      with:
        ruby-version: 3.2

    - name: Install Kamal
      run: gem install kamal

    - name: Deploy
      env:
        KAMAL_REGISTRY_PASSWORD: ${{ secrets.KAMAL_REGISTRY_PASSWORD }}
        SECRET_KEY: ${{ secrets.SECRET_KEY }}
      run: |
        kamal deploy
```

---

## 롤백 (Rollback)

```bash
# Kamal (이전 버전으로 롤백)
kamal app rollback

# Docker Compose (특정 이미지로 롤백)
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d omnivibepro/backend:v1.0.0
```

---

## 비용 예상 (월간)

| 항목 | 비용 |
|------|------|
| **서버** (Vultr 8GB) | $48 |
| **도메인** (omnivibepro.com) | $1 |
| **Cloudflare** (Free) | $0 |
| **Logfire** | $20 |
| **Sentry** | $0 (무료 플랜) |
| **S3 백업** | $5 |
| **Total** | **$74/월** |

**PostgreSQL 대비**: -$100/월 (RDS 비용 절감)

---

## 배포 완료 체크리스트

- [ ] 서버 준비 완료
- [ ] Docker 설치
- [ ] Kamal 설정
- [ ] 환경 변수 설정
- [ ] Accessories 배포 (Redis, Neo4j)
- [ ] 앱 배포
- [ ] HTTPS 인증서
- [ ] 도메인 연결
- [ ] 모니터링 설정
- [ ] 백업 스크립트 Cron 등록
- [ ] 방화벽 설정
- [ ] Health Check 확인
- [ ] 성능 테스트

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro DevOps Team
