# Vultr 빠른 시작 가이드

> **10분 안에 Vultr에 OmniVibe Pro 배포하기**

---

## 🚀 빠른 배포 (3단계)

### 1단계: Vultr 서버 생성 (3분)

1. **Vultr 접속**: https://my.vultr.com
2. **Deploy New Server** 클릭
3. 설정:
   - **Type**: Cloud Compute
   - **Location**: Seoul (한국)
   - **Image**: Ubuntu 22.04
   - **Plan**: 8GB RAM ($48/월)
   - **SSH Key**: 추가 (또는 나중에)
4. **Deploy Now** 클릭
5. **IP 주소 확인**: `123.456.789.012` (예시)

---

### 2단계: 서버 초기 설정 (5분)

```bash
# 로컬에서 SSH 접속
ssh root@123.456.789.012

# 비밀번호 입력 (Vultr 이메일 확인)
```

#### 자동 설정 스크립트 실행

```bash
# 스크립트 다운로드
curl -fsSL https://raw.githubusercontent.com/your-username/OmniVibePro/main/scripts/vultr_setup.sh -o setup.sh

# 실행
bash setup.sh
```

**또는 수동 설정**:

```bash
# 시스템 업데이트
apt update && apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com | sh

# Docker Compose 설치
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 배포 사용자 생성
adduser deploy
usermod -aG sudo,docker deploy

# 방화벽 설정
ufw allow 22,80,443/tcp
ufw enable
```

---

### 3단계: 프로젝트 배포 (2분)

```bash
# deploy 사용자로 전환
su - deploy

# 프로젝트 클론
git clone https://github.com/your-username/OmniVibePro.git
cd OmniVibePro

# .env 파일 생성
nano .env
```

#### .env 파일 내용 (필수만)

```bash
ENV=production
DEBUG=False
SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(32))">

DATABASE_URL=sqlite:///omni_db.sqlite
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=<강력한 비밀번호>

ELEVENLABS_API_KEY=sk_...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
STRIPE_SECRET_KEY=sk_live_...

FORCE_HTTPS=True
```

#### 배포 실행

```bash
# Docker Compose로 시작
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인 (Ctrl+C로 종료)
docker-compose -f docker-compose.prod.yml logs -f
```

---

## ✅ 배포 확인

### Health Check

```bash
curl http://localhost:8000/health
# {"status":"online","version":"1.0.0"}
```

### 브라우저에서 확인

- **API**: http://123.456.789.012:8000/docs
- **Frontend**: http://123.456.789.012:3020

---

## 🌐 도메인 연결 (선택사항)

### 1. DNS A 레코드 추가

**도메인 관리자** (Cloudflare, GoDaddy 등)에서:

```
Type: A
Name: @
Value: 123.456.789.012
```

```
Type: A
Name: api
Value: 123.456.789.012
```

### 2. Nginx + SSL 설정

```bash
# Nginx 설치
sudo apt install nginx certbot python3-certbot-nginx -y

# Nginx 설정
sudo nano /etc/nginx/sites-available/omnivibe
```

**내용**:
```nginx
server {
    listen 80;
    server_name api.omnivibepro.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 활성화
sudo ln -s /etc/nginx/sites-available/omnivibe /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL 설정
sudo certbot --nginx -d api.omnivibepro.com
```

---

## 🔄 업데이트 배포

```bash
cd /home/deploy/OmniVibePro
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 💾 백업 자동화

```bash
# Cron 설정
crontab -e

# 매일 새벽 2시 백업
0 2 * * * /home/deploy/OmniVibePro/backend/scripts/backup_db.sh
```

---

## 📞 도움이 필요하면?

- **문서**: `/docs/VULTR_DEPLOYMENT_GUIDE.md`
- **이슈**: GitHub Issues
- **Discord**: https://discord.gg/omnivibepro

---

## 💰 비용

| 항목 | 월 비용 |
|------|---------|
| Vultr 서버 (8GB) | $48 |
| 도메인 | $12/년 |
| **Total** | **$48/월** |

---

**Happy Deploying! 🚀**
