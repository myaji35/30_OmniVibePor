# Vultr Deployment Guide - OmniVibe Pro

> **프로덕션 환경 배포 가이드**
> **Vultr VPS + Docker Compose + Nginx + Let's Encrypt SSL**

---

## 📋 목차

1. [Prerequisites](#prerequisites)
2. [Vultr VPS 설정](#vultr-vps-설정)
3. [서버 초기 설정](#서버-초기-설정)
4. [도메인 및 DNS 설정](#도메인-및-dns-설정)
5. [애플리케이션 배포](#애플리케이션-배포)
6. [SSL 인증서 설정](#ssl-인증서-설정)
7. [모니터링 및 관리](#모니터링-및-관리)
8. [트러블슈팅](#트러블슈팅)

---

## Prerequisites

### 필요한 것들

- **Vultr 계정** (https://www.vultr.com)
- **도메인** (예: omnivibepro.com)
- **API Keys** (ElevenLabs, OpenAI, Anthropic, Cloudinary)
- **Git & Docker 지식** (기본)

### 권장 VPS 사양

| 구성 요소 | 최소 사양 | 권장 사양 |
|----------|----------|----------|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 8 GB | 16 GB |
| Storage | 80 GB SSD | 160 GB NVMe |
| Bandwidth | 4 TB | 8 TB |

**권장 플랜**: Vultr Cloud Compute - $40/month (8 vCPU, 16GB RAM, 160GB SSD)

---

## Vultr VPS 설정

### 1. VPS 인스턴스 생성

1. Vultr 대시보드 접속
2. **Deploy New Server** 클릭
3. **Server Type**: Cloud Compute
4. **Location**: Seoul, KR (가장 가까운 지역)
5. **Server Image**: Ubuntu 22.04 LTS x64
6. **Server Size**: $40/mo (8 vCPU, 16GB RAM)
7. **Additional Features**:
   - ✅ Enable Auto Backups
   - ✅ Enable IPv6
   - ✅ Enable Private Networking
8. **Server Hostname**: omnivibe-production
9. **Deploy Now** 클릭

### 2. SSH 접속 정보 확인

VPS 생성 후 대시보드에서 확인:
- **IP Address**: `123.456.789.0`
- **Username**: `root`
- **Password**: 이메일로 전송됨

---

## 서버 초기 설정

### 1. SSH 접속

```bash
ssh root@123.456.789.0
```

### 2. 시스템 업데이트

```bash
apt update && apt upgrade -y
```

### 3. 필수 패키지 설치

```bash
apt install -y \
  curl \
  git \
  vim \
  htop \
  ufw \
  fail2ban
```

### 4. Docker 설치

```bash
# Docker 공식 설치 스크립트
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose 설치
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Docker 버전 확인
docker --version
docker-compose --version
```

### 5. 방화벽 설정 (UFW)

```bash
# SSH 포트 열기
ufw allow 22/tcp

# HTTP/HTTPS 포트 열기
ufw allow 80/tcp
ufw allow 443/tcp

# 방화벽 활성화
ufw enable

# 상태 확인
ufw status
```

### 6. 사용자 계정 생성 (선택사항)

```bash
# omnivibe 사용자 생성
adduser omnivibe
usermod -aG sudo omnivibe
usermod -aG docker omnivibe

# omnivibe 사용자로 전환
su - omnivibe
```

---

## 도메인 및 DNS 설정

### 1. 도메인 DNS 설정

도메인 등록 업체(가비아, Cloudflare 등)에서 다음 A 레코드 추가:

| Type | Name | Value (VPS IP) | TTL |
|------|------|----------------|-----|
| A | @ | 123.456.789.0 | 3600 |
| A | www | 123.456.789.0 | 3600 |
| A | api | 123.456.789.0 | 3600 |

### 2. DNS 전파 확인

```bash
# 로컬 머신에서 실행
nslookup omnivibepro.com
nslookup api.omnivibepro.com

# 또는
dig omnivibepro.com
dig api.omnivibepro.com
```

DNS 전파는 최대 24시간 소요 (보통 1-2시간)

---

## 애플리케이션 배포

### 1. 프로젝트 클론

```bash
cd /home/omnivibe
git clone https://github.com/your-org/OmniVibePro.git
cd OmniVibePro
```

### 2. 환경 변수 설정

```bash
# .env.production 생성
cp .env.production.template .env.production
nano .env.production
```

**필수 환경 변수**:
```bash
# Neo4j
NEO4J_PASSWORD=your_secure_password_here

# API Keys
ELEVENLABS_API_KEY=sk_...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
```

### 3. 배포 실행

```bash
./deploy-vultr.sh production
```

배포 스크립트는 자동으로:
- ✅ Docker 이미지 빌드
- ✅ 컨테이너 시작 (Backend, Frontend, Redis, Neo4j, Celery, Nginx)
- ✅ Neo4j 스키마 초기화
- ✅ Health Check 실행

### 4. 배포 상태 확인

```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.production.yml ps

# 로그 확인
docker logs -f omnivibe-backend
docker logs -f omnivibe-celery-worker
docker logs -f omnivibe-nginx
```

**정상 배포 시 출력**:
```
✅ omnivibe-backend       Up (healthy)
✅ omnivibe-frontend      Up (healthy)
✅ omnivibe-redis         Up (healthy)
✅ omnivibe-neo4j         Up (healthy)
✅ omnivibe-celery-worker Up
✅ omnivibe-nginx         Up (healthy)
```

---

## SSL 인증서 설정

### 1. Certbot으로 Let's Encrypt SSL 발급

```bash
# Certbot 컨테이너로 인증서 발급
docker run -it --rm \
  -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d omnivibepro.com \
  -d www.omnivibepro.com \
  -d api.omnivibepro.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email
```

### 2. SSL 인증서 파일 확인

```bash
ls -la nginx/ssl/live/omnivibepro.com/
# fullchain.pem  (인증서 체인)
# privkey.pem    (개인 키)
```

### 3. Nginx 설정 업데이트

SSL 인증서 경로를 Nginx 설정에 반영:

```bash
nano nginx/nginx.conf
```

```nginx
ssl_certificate /etc/nginx/ssl/live/omnivibepro.com/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/live/omnivibepro.com/privkey.pem;
```

### 4. Nginx 재시작

```bash
docker exec omnivibe-nginx nginx -s reload
```

### 5. SSL 자동 갱신 설정

```bash
# Crontab 편집
crontab -e

# 매월 1일 새벽 3시 SSL 갱신
0 3 1 * * docker run --rm -v /home/omnivibe/OmniVibePro/nginx/ssl:/etc/letsencrypt certbot/certbot renew --quiet && docker exec omnivibe-nginx nginx -s reload
```

---

## 모니터링 및 관리

### 1. 실시간 로그 모니터링

```bash
# 전체 로그
docker-compose -f docker-compose.production.yml logs -f

# Backend만
docker logs -f omnivibe-backend

# Celery Worker만
docker logs -f omnivibe-celery-worker
```

### 2. 서버 리소스 모니터링

```bash
# CPU, 메모리 사용량
htop

# Docker 컨테이너별 리소스
docker stats

# 디스크 사용량
df -h
```

### 3. Neo4j 데이터베이스 확인

```bash
# Neo4j Browser 접속
# URL: http://123.456.789.0:7474
# ID: neo4j
# PW: (NEO4J_PASSWORD 값)

# Cypher Shell 접속
docker exec -it omnivibe-neo4j cypher-shell -u neo4j -p omnivibe2026

# 스크립트 개수 확인
MATCH (s:Script) RETURN count(s);
```

### 4. Redis 상태 확인

```bash
# Redis CLI 접속
docker exec -it omnivibe-redis redis-cli

# Celery 큐 상태 확인
LLEN celery
KEYS *
```

### 5. 백업 자동화

```bash
# 백업 스크립트 생성
nano /home/omnivibe/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/omnivibe/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# SQLite 백업
docker exec omnivibe-backend cp /app/omni_db.sqlite /tmp/
docker cp omnivibe-backend:/tmp/omni_db.sqlite $BACKUP_DIR/

# Neo4j 백업
docker exec omnivibe-neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j-backup.dump
docker cp omnivibe-neo4j:/tmp/neo4j-backup.dump $BACKUP_DIR/

# 오래된 백업 삭제 (7일 이상)
find /home/omnivibe/backups/* -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

```bash
chmod +x /home/omnivibe/backup.sh

# Crontab에 추가 (매일 새벽 4시)
crontab -e
0 4 * * * /home/omnivibe/backup.sh >> /home/omnivibe/backup.log 2>&1
```

---

## 트러블슈팅

### 문제 1: 컨테이너가 시작되지 않음

**증상**:
```
Error: Cannot start container omnivibe-backend
```

**해결 방법**:
```bash
# 로그 확인
docker logs omnivibe-backend

# 컨테이너 재생성
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

### 문제 2: Nginx 502 Bad Gateway

**증상**:
브라우저에서 502 Bad Gateway 에러

**해결 방법**:
```bash
# Backend 상태 확인
docker ps | grep backend

# Backend 재시작
docker restart omnivibe-backend

# Nginx 재시작
docker restart omnivibe-nginx
```

### 문제 3: Celery Worker가 작업을 처리하지 않음

**증상**:
오디오 생성이 대기 상태로 멈춤

**해결 방법**:
```bash
# Worker 로그 확인
docker logs -f omnivibe-celery-worker

# Worker 재시작
docker restart omnivibe-celery-worker

# Redis 큐 확인
docker exec -it omnivibe-redis redis-cli
LLEN celery
```

### 문제 4: Neo4j 연결 실패

**증상**:
```
Failed to connect to Neo4j: ServiceUnavailable
```

**해결 방법**:
```bash
# Neo4j 상태 확인
docker logs omnivibe-neo4j

# Neo4j 재시작
docker restart omnivibe-neo4j

# 비밀번호 확인
echo $NEO4J_PASSWORD
```

### 문제 5: 메모리 부족

**증상**:
```
Cannot allocate memory
```

**해결 방법**:
```bash
# 메모리 사용량 확인
free -h
docker stats

# 불필요한 컨테이너 제거
docker system prune -a

# Swap 메모리 추가 (4GB)
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## 유용한 명령어 모음

### 서비스 관리

```bash
# 전체 서비스 시작
docker-compose -f docker-compose.production.yml up -d

# 전체 서비스 중지
docker-compose -f docker-compose.production.yml down

# 특정 서비스 재시작
docker restart omnivibe-backend

# 전체 서비스 재시작
docker-compose -f docker-compose.production.yml restart
```

### 로그 확인

```bash
# 최근 100줄 로그
docker logs --tail 100 omnivibe-backend

# 실시간 로그 (Ctrl+C로 종료)
docker logs -f omnivibe-backend

# 특정 시간대 로그
docker logs --since 2026-02-08T10:00:00 omnivibe-backend
```

### 데이터베이스

```bash
# SQLite 백업
docker cp omnivibe-backend:/app/omni_db.sqlite ./omni_db_backup.sqlite

# Neo4j Cypher Shell
docker exec -it omnivibe-neo4j cypher-shell -u neo4j -p omnivibe2026

# Redis CLI
docker exec -it omnivibe-redis redis-cli
```

---

## 성능 최적화 팁

### 1. Docker Compose 병렬 처리

```yaml
# docker-compose.production.yml
celery-worker:
  # ...
  deploy:
    replicas: 3  # Worker 3개 병렬 실행
```

### 2. Nginx 캐싱

```nginx
# nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
}
```

### 3. Redis 메모리 최적화

```bash
# Redis 설정
docker exec -it omnivibe-redis redis-cli CONFIG SET maxmemory 2gb
docker exec -it omnivibe-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## 보안 체크리스트

- [ ] SSH 비밀번호 로그인 비활성화 (SSH Key만 허용)
- [ ] UFW 방화벽 활성화
- [ ] Fail2Ban으로 무차별 대입 공격 방어
- [ ] Neo4j 비밀번호 변경 (기본값 사용 금지)
- [ ] API Keys 환경 변수로 관리 (코드에 하드코딩 금지)
- [ ] SSL 인증서 자동 갱신 설정
- [ ] Nginx rate limiting 활성화
- [ ] 정기 백업 자동화
- [ ] Docker 이미지 최신화 (보안 패치)

---

## 참고 자료

- **Vultr 문서**: https://www.vultr.com/docs/
- **Docker Compose 문서**: https://docs.docker.com/compose/
- **Nginx 문서**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **OmniVibe Pro API 문서**: http://localhost:8000/docs

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro DevOps Team
