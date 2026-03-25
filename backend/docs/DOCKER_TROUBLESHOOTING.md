# Docker 코드 반영 이슈 분석 및 해결

## 문제 상황

Python 코드를 수정한 후 `docker compose restart`를 실행해도 변경사항이 컨테이너에 반영되지 않음.

## 근본 원인

### 1. 볼륨 마운트 비활성화 상태

**docker-compose.yml (12-13번 줄):**
```yaml
volumes:
  # Colima 볼륨 마운트 이슈로 주석 처리
  # - ./app:/app/app
  - ./outputs:/app/outputs
```

- **현재 상태**: `./app:/app/app` 볼륨 마운트가 주석 처리됨
- **이유**: Colima(macOS Docker 런타임)의 볼륨 마운트 성능 이슈

### 2. 코드 복사 시점

**Dockerfile (25번 줄):**
```dockerfile
# 애플리케이션 코드 복사
COPY . .
```

- **빌드 시점**: 이미지 빌드 시 호스트의 코드를 컨테이너 이미지에 복사
- **문제**: 이미지 빌드 후에는 이미지 내부 코드가 고정됨

### 3. Docker Compose 동작 방식

#### `docker compose restart`
- 기존 컨테이너를 정지 후 재시작
- **이미지 재빌드 안함**
- **볼륨 마운트가 없으면** 이미지 내부의 고정된 코드만 사용
- ❌ 코드 변경사항 반영 안됨

#### `docker compose up -d --build`
- 이미지 재빌드
- 새 이미지로 컨테이너 재생성
- ✅ 최신 코드 반영됨

## 코드 반영 흐름 비교

### 볼륨 마운트 활성화 시 (개발 환경)
```
1. 호스트에서 코드 수정
2. docker compose restart
   → 컨테이너 재시작
   → 볼륨 마운트된 코드 자동 반영 ✅
3. 변경사항 즉시 적용
```

### 볼륨 마운트 비활성화 시 (현재 환경)
```
1. 호스트에서 코드 수정
2. docker compose restart
   → 컨테이너 재시작
   → 이미지 내부 코드는 그대로 ❌
3. 변경사항 반영 안됨

올바른 방법:
1. 호스트에서 코드 수정
2. docker compose down
3. docker compose up -d --build
   → 이미지 재빌드 (COPY . . 실행)
   → 최신 코드로 이미지 생성 ✅
4. 변경사항 반영됨
```

## 해결 방법

### 방법 1: 코드 변경 시마다 재빌드 (현재 사용)

```bash
# 전체 컨테이너 중단 및 재빌드
cd /path/to/backend
docker compose down
find . -name "._*" -delete  # macOS 메타데이터 파일 제거
docker compose up -d --build

# 특정 서비스만 재빌드 (API만)
docker compose up -d --build api

# 특정 서비스만 재빌드 (Celery Worker만)
docker compose up -d --build celery_worker
```

**장점:**
- Colima 볼륨 마운트 이슈 회피
- 운영 환경과 동일한 구조

**단점:**
- 코드 수정 시마다 재빌드 필요 (약 10-20초 소요)
- 개발 속도 저하

### 방법 2: 볼륨 마운트 활성화 (권장 - 개발 환경)

**docker-compose.yml 수정:**
```yaml
services:
  api:
    volumes:
      - ./app:/app/app  # 주석 해제
      - ./outputs:/app/outputs

  celery_worker:
    volumes:
      - ./app:/app/app  # 주석 해제
      - ./outputs:/app/outputs

  celery_beat:
    volumes:
      - ./app:/app/app  # 주석 해제
      - ./outputs:/app/outputs
```

**적용 후:**
```bash
docker compose down
docker compose up -d
```

**이후 코드 변경 시:**
```bash
# FastAPI는 자동 리로드
# Celery는 재시작 필요
docker compose restart celery_worker
```

**장점:**
- 코드 변경 즉시 반영 (FastAPI auto-reload)
- 개발 속도 향상

**단점:**
- Colima 환경에서 I/O 성능 저하 가능
- 파일 감지 지연 발생 가능

### 방법 3: Docker Desktop 사용

Colima 대신 Docker Desktop 사용 시 볼륨 마운트 성능 개선됨.

```bash
# Colima 중지
colima stop

# Docker Desktop 설치 및 실행
# https://www.docker.com/products/docker-desktop/

# 볼륨 마운트 활성화 후 사용
```

## 베스트 프랙티스

### 개발 환경
1. 볼륨 마운트 활성화
2. FastAPI auto-reload 활용
3. Celery 변경 시에만 `docker compose restart celery_worker`

### 운영 환경
1. 볼륨 마운트 비활성화
2. 이미지 빌드 후 배포
3. 코드가 이미지 내부에 고정되어 안정성 확보

## 체크리스트

### 코드 변경사항이 반영 안될 때

- [ ] 볼륨 마운트 상태 확인 (`docker-compose.yml`)
- [ ] `docker compose restart` 대신 `docker compose up -d --build` 사용
- [ ] macOS 메타데이터 파일 제거 (`find . -name "._*" -delete`)
- [ ] 컨테이너 로그 확인 (`docker compose logs api`)
- [ ] 이미지 캐시 문제 시 `docker compose build --no-cache`

### Celery 작업 변경사항이 반영 안될 때

Celery Worker는 시작 시 코드를 메모리에 로드하므로 반드시 재시작 필요:

```bash
# 볼륨 마운트 있을 때
docker compose restart celery_worker

# 볼륨 마운트 없을 때
docker compose up -d --build celery_worker
```

## 요약

| 상황 | 명령어 | 소요 시간 | 적용 여부 |
|------|--------|-----------|-----------|
| 볼륨 마운트 O + 코드 수정 | `docker compose restart` | 2초 | ✅ 반영됨 |
| 볼륨 마운트 X + 코드 수정 | `docker compose restart` | 2초 | ❌ 반영 안됨 |
| 볼륨 마운트 X + 코드 수정 | `docker compose up -d --build` | 15초 | ✅ 반영됨 |
| 이미지 캐시 문제 | `docker compose build --no-cache && docker compose up -d` | 60초 | ✅ 반영됨 |

## 현재 프로젝트 상태

- **볼륨 마운트**: ❌ 비활성화 (ExFAT 파일 시스템 이슈)
- **코드 반영 방법**: `docker compose down && docker compose up -d --build`
- **권장 사항**: 아래 ExFAT 해결책 참고

## ExFAT 외장 SSD 볼륨 마운트 이슈

### 문제 진단 (2026-02-02)

**증상:**
- `./app:/app/app` 볼륨 마운트 활성화 시 컨테이너 내부 `/app/app` 디렉토리가 빈 상태
- `ERROR: Error loading ASGI app. Could not import module "app.main"` 발생
- 호스트에는 파일이 정상적으로 존재하지만 Docker 컨테이너에서 접근 불가

**근본 원인:**
- **ExFAT 파일 시스템**은 Unix 권한/속성을 지원하지 않음
- Colima VirtioFS가 ExFAT 볼륨을 정상적으로 마운트하지 못함
- 기본적으로 Colima는 `$HOME` 디렉토리만 마운트하며, `/Volumes` 경로는 자동 마운트 대상이 아님

**검증 결과:**
```bash
# 테스트 명령어
$ docker run --rm -v "/Volumes/Extreme SSD/.../app:/test" alpine ls -la /test
total 8
drwxr-xr-x    2 root     root          4096 Feb  1 08:53 .
drwxr-xr-x    1 root     root          4096 Feb  1 15:06 ..
# → 빈 디렉토리 (파일 동기화 실패)

# Colima 상태
$ colima status
mountType: virtiofs  # VirtioFS 활성화되어 있음
# → VirtioFS는 정상이지만 ExFAT 호환 문제
```

### 해결책

#### 옵션 1: 프로젝트를 APFS/HFS+ 볼륨으로 이동 (권장)

**장점:**
- 완벽한 파일 시스템 호환성
- 볼륨 마운트 성능 최적화
- Unix 권한 완벽 지원

**방법:**
```bash
# 1. 내장 SSD 또는 APFS 포맷 외장 SSD로 프로젝트 이동
cp -R "/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro" \
      ~/Projects/OmniVibePro

# 2. docker-compose.yml 볼륨 마운트 활성화
# (파일 내 주석 해제)

# 3. 재시작
cd ~/Projects/OmniVibePro/backend
docker compose down
docker compose up -d

# 4. 이후 코드 변경은 자동 반영 (FastAPI auto-reload)
```

#### 옵션 2: Colima에 /Volumes 경로 명시적 마운트

**주의:** Colima 재시작 필요, 기존 컨테이너/볼륨 삭제됨

**방법:**
```bash
# 1. Colima 중지
colima stop

# 2. Colima 설정 편집
vim ~/.colima/default/colima.yaml

# 3. mounts 섹션에 추가:
mounts:
  - location: /Volumes/Extreme SSD
    writable: true

# 4. Colima 재시작
colima start

# 5. docker-compose.yml 볼륨 마운트 활성화
# 6. docker compose up -d
```

**장점:**
- ExFAT 외장 SSD 그대로 사용 가능
- 프로젝트 이동 불필요

**단점:**
- Colima 재시작 시 모든 컨테이너/볼륨 재생성 필요
- ExFAT I/O 성능이 APFS보다 느릴 수 있음

#### 옵션 3: Docker Desktop 사용

Docker Desktop은 `/Volumes` 자동 마운트를 더 잘 지원합니다.

```bash
# 1. Colima 중지
colima stop

# 2. Docker Desktop 설치
# https://www.docker.com/products/docker-desktop/

# 3. Settings → Resources → File Sharing에서
#    "/Volumes/Extreme SSD" 추가

# 4. docker-compose.yml 볼륨 마운트 활성화
# 5. docker compose up -d
```

**장점:**
- GUI 기반 설정
- 더 나은 macOS 통합

**단점:**
- 유료 라이선스 필요 (상업용)
- Colima보다 무거움

#### 옵션 4: 현재 워크플로우 유지 (임시 방안)

볼륨 마운트 없이 이미지 재빌드 방식으로 개발 (현재 방식)

```bash
# 코드 수정 후
docker compose down
docker compose up -d --build

# 빌드 시간: ~15초
```

**장점:**
- 추가 설정 불필요
- 운영 환경과 동일한 구조

**단점:**
- 코드 변경 시마다 재빌드 필요
- 개발 속도 저하

### 권장 사항

1. **단기**: 옵션 4 유지 (현재 방식)
2. **중장기**: 옵션 1 (프로젝트를 APFS 볼륨으로 이동)
   - 내장 SSD `~/Projects`로 이동 권장
   - ExFAT 외장 SSD는 백업/아카이브 용도로 사용

### 성능 비교 예상치

| 환경 | 코드 변경 반영 시간 | FastAPI Auto-Reload |
|------|---------------------|---------------------|
| APFS + 볼륨 마운트 | 즉시 (0.5초) | ✅ 지원 |
| ExFAT + 옵션 2 | 1-3초 | ⚠️ 느림 |
| 재빌드 방식 (현재) | 15초 | ❌ 미지원 |
