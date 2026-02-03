# SQLite3 DB 백업 자동화 가이드

## 개요

OmniVibe Pro의 프로덕션 데이터베이스(`omnivibe.db`)를 자동으로 백업하고 필요 시 복구하는 시스템입니다.

**현재 상태**
- 프로덕션 DB: `frontend/data/omnivibe.db` (144 KB, 93개 레코드)
- 백업 저장소: `frontend/data/backups/`
- 보관 정책: 최근 7일 백업만 유지

---

## 빠른 시작

### 1. 수동 백업 (언제든지)

```bash
./scripts/backup_db.sh
```

**출력 예시**:
```
⏳ 백업 시작: 2026-02-03 02:36:42
✅ 백업 완료: omnivibe_20260203_023642.db (144K)
🧹 오래된 백업 정리 중...

📊 백업 현황:
  /path/to/omnivibe_20260203_023642.db (144K)
💾 총 백업 개수: 1개
```

### 2. 데이터 복구

```bash
# 사용 가능한 백업 목록 확인
./scripts/restore_db.sh

# 특정 백업에서 복구
./scripts/restore_db.sh omnivibe_20260203_023642.db
```

**복구 시 안전 장치**:
- 복구 전 현재 DB를 안전 백업으로 저장
- 복구 취소 옵션 제공
- 복구 실패 시 되돌릴 수 있는 방법 안내

---

## 자동 백업 설정 (cron)

### macOS에서 설정

#### 방법 1: crontab 편집기 사용 (권장)

```bash
# crontab 편집 시작
crontab -e
```

다음 중 원하는 스케줄을 추가하세요:

**매일 3시 AM (권장)**
```bash
0 3 * * * cd /path/to/OmniVibePro && ./scripts/backup_db.sh >> ~/logs/db_backup.log 2>&1
```

**매 시간마다**
```bash
0 * * * * cd /path/to/OmniVibePro && ./scripts/backup_db.sh >> ~/logs/db_backup.log 2>&1
```

**평일 오전 9시**
```bash
0 9 * * 1-5 cd /path/to/OmniVibePro && ./scripts/backup_db.sh >> ~/logs/db_backup.log 2>&1
```

**매 6시간마다**
```bash
0 */6 * * * cd /path/to/OmniVibePro && ./scripts/backup_db.sh >> ~/logs/db_backup.log 2>&1
```

#### 방법 2: 설정 파일로 추가

```bash
# 로그 디렉토리 생성
mkdir -p ~/logs

# 현재 crontab 저장
crontab -l > /tmp/crontab_backup.txt

# 새로운 항목 추가
echo "0 3 * * * cd /path/to/OmniVibePro && ./scripts/backup_db.sh >> ~/logs/db_backup.log 2>&1" >> /tmp/crontab_backup.txt

# 새로운 crontab 설치
crontab /tmp/crontab_backup.txt
```

#### 방법 3: launchd를 사용한 고급 설정 (macOS 전용)

`~/Library/LaunchAgents/com.omnivibe.db.backup.plist` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omnivibe.db.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/path/to/OmniVibePro/scripts/backup_db.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>3</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    <key>StandardOutPath</key>
    <string>/var/log/omnivibe_backup.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/omnivibe_backup_error.log</string>
</dict>
</plist>
```

설치:
```bash
launchctl load ~/Library/LaunchAgents/com.omnivibe.db.backup.plist
```

---

## cron 스케줄 참고

```
┌───────────── 분 (0-59)
│ ┌───────────── 시간 (0-23)
│ │ ┌───────────── 일 (1-31)
│ │ │ ┌───────────── 월 (1-12)
│ │ │ │ ┌───────────── 요일 (0-7, 0 또는 7 = 일요일)
│ │ │ │ │
│ │ │ │ │
* * * * * /path/to/command
```

**예시**:
- `0 3 * * *` = 매일 3:00 AM
- `0 */6 * * *` = 매 6시간마다
- `30 2 * * 1-5` = 평일 오전 2:30
- `0 0 1 * *` = 매달 1일 자정
- `*/15 * * * *` = 15분마다

---

## 설정 확인

### 현재 crontab 확인

```bash
crontab -l
```

### 백업 로그 확인

```bash
# 마지막 10개 백업 로그 보기
tail -10 ~/logs/db_backup.log

# 실시간 로그 확인
tail -f ~/logs/db_backup.log
```

### 백업 파일 확인

```bash
# 백업 디렉토리 내용
ls -lh frontend/data/backups/

# 가장 최신 백업
ls -lth frontend/data/backups/ | head -5
```

---

## 트러블슈팅

### 백업이 실행되지 않음

1. **crontab 확인**
   ```bash
   crontab -l
   ```

2. **권한 확인**
   ```bash
   ls -l scripts/backup_db.sh
   # -rwx------이어야 함
   ```

3. **경로 확인**
   ```bash
   # 절대 경로로 변경
   which bash  # /bin/bash 확인
   pwd         # 절대 경로 확인
   ```

4. **로그 확인**
   ```bash
   # macOS 시스템 로그
   log stream --predicate 'eventMessage contains "backup"'
   ```

### 백업 파일이 손상됨

1. **파일 무결성 확인**
   ```bash
   # SQLite 데이터베이스 검증
   sqlite3 frontend/data/backups/omnivibe_20260203_023642.db "PRAGMA integrity_check;"
   # 결과: "ok" 또는 "corruption reported"
   ```

2. **손상된 백업 삭제**
   ```bash
   rm frontend/data/backups/omnivibe_20260203_023642.db
   ```

### 복구 실패

1. **안전 백업에서 복구**
   ```bash
   # 생성된 안전 백업 파일 확인
   ls -lt frontend/data/omnivibe_before_restore_*.db | head -1

   # 복구
   cp frontend/data/omnivibe_before_restore_20260203_023642.db frontend/data/omnivibe.db
   ```

---

## 백업 정책

| 항목 | 설정 |
|------|------|
| 백업 주기 | 24시간 (수정 권장) |
| 보관 기간 | 7일 |
| 저장 위치 | `frontend/data/backups/` |
| 명명 규칙 | `omnivibe_YYYYMMDD_HHMMSS.db` |
| 안전 백업 | 복구 시 자동 생성 |

---

## 성능 고려사항

**백업 시간**:
- 현재 DB 크기: 144 KB
- 예상 백업 시간: < 1초

**디스크 공간**:
- 일일 백업: ~144 KB/일
- 7일 보관: ~1 MB
- 1년(365일): ~52 MB (충분한 여유)

---

## 추가 기능

### 압축 백업 (선택사항)

더 작은 크기로 저장하려면 `backup_db.sh` 수정:

```bash
# 기존
cp "$DB_PATH" "$BACKUP_FILE"

# 변경 (gzip 압축)
gzip -c "$DB_PATH" > "$BACKUP_FILE.gz"
```

복구 시:
```bash
gunzip -c "$BACKUP_FILE.gz" > "$DB_PATH"
```

### 원격 백업 (선택사항)

AWS S3, Google Cloud Storage, Dropbox 등으로 백업:

```bash
# AWS S3 예시
aws s3 cp "$BACKUP_FILE" s3://my-bucket/omnivibe-backups/

# Google Drive 예시 (gdrive 설치 필요)
gdrive upload "$BACKUP_FILE"
```

---

## 자주 묻는 질문

**Q: 백업이 얼마나 자주 필요한가?**
A: 데이터 변경 빈도에 따라 다릅니다.
- 실시간 변경: 매시간
- 일일 변경: 매일 3 AM
- 주간 변경: 주 1-2회

**Q: 백업 파일을 얼마나 오래 보관해야 하나?**
A: 현재 7일 설정입니다. 필요에 따라:
- 수정: `backup_db.sh`의 `mtime +7` 변경
- 예: `mtime +30` (30일), `mtime +0` (당일만)

**Q: 여러 백업 버전에서 선택할 수 있나?**
A: 네, `./scripts/restore_db.sh` 실행 시 가능한 백업 목록을 볼 수 있습니다.

**Q: 자동 백업을 중지하려면?**
A: `crontab -e` 후 해당 줄을 주석 또는 삭제하세요.

---

## 체크리스트

- [ ] 백업 스크립트 테스트 (`./scripts/backup_db.sh`)
- [ ] 복구 스크립트 테스트 (`./scripts/restore_db.sh`)
- [ ] cron 설정 완료
- [ ] 로그 디렉토리 생성 (`mkdir -p ~/logs`)
- [ ] 백업 로그 확인 (`tail ~/logs/db_backup.log`)
- [ ] 월 1회 복구 테스트 실행

---

**마지막 업데이트**: 2026-02-03
**스크립트 버전**: 1.0
