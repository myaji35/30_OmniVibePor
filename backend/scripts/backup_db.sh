#!/bin/bash

# SQLite3 데이터베이스 자동 백업 스크립트
# Cron 설정 예시: 0 2 * * * /path/to/backup_db.sh

set -e  # 에러 발생 시 종료

# 설정
DB_PATH="/Volumes/Extreme SSD/02_GitHub.nosync/0030_OmniVibePro/backend/omni_db.sqlite"
BACKUP_DIR="/Volumes/Extreme SSD/02_GitHub.nosync/0030_OmniVibePro/backend/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="omni_db_backup_${TIMESTAMP}.sqlite"
KEEP_DAYS=7  # 7일 이상 된 백업 삭제

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

echo "🚀 Starting database backup..."
echo "  Source: $DB_PATH"
echo "  Destination: $BACKUP_DIR/$BACKUP_NAME"

# 1. SQLite 백업 (VACUUM INTO 사용 - 가장 안전)
if command -v sqlite3 &> /dev/null; then
    sqlite3 "$DB_PATH" "VACUUM INTO '$BACKUP_DIR/$BACKUP_NAME'"
    echo "✓ Backup created using VACUUM INTO"
else
    # sqlite3 명령어가 없으면 파일 복사
    cp "$DB_PATH" "$BACKUP_DIR/$BACKUP_NAME"

    # WAL 파일도 백업 (존재하는 경우)
    if [ -f "${DB_PATH}-wal" ]; then
        cp "${DB_PATH}-wal" "${BACKUP_DIR}/${BACKUP_NAME}-wal"
    fi

    # SHM 파일도 백업 (존재하는 경우)
    if [ -f "${DB_PATH}-shm" ]; then
        cp "${DB_PATH}-shm" "${BACKUP_DIR}/${BACKUP_NAME}-shm"
    fi

    echo "✓ Backup created using file copy"
fi

# 2. 백업 파일 압축 (gzip)
gzip "$BACKUP_DIR/$BACKUP_NAME"
echo "✓ Backup compressed: ${BACKUP_NAME}.gz"

# 3. 백업 파일 크기 확인
BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.gz" | cut -f1)
echo "  Backup size: $BACKUP_SIZE"

# 4. 오래된 백업 삭제 (7일 이상)
echo "🧹 Cleaning up old backups (older than $KEEP_DAYS days)..."
find "$BACKUP_DIR" -name "omni_db_backup_*.sqlite.gz" -type f -mtime +$KEEP_DAYS -delete
echo "✓ Old backups cleaned up"

# 5. 현재 백업 개수 확인
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "omni_db_backup_*.sqlite.gz" -type f | wc -l | tr -d ' ')
echo "  Total backups: $BACKUP_COUNT"

echo "✅ Backup completed successfully!"

# 6. (선택사항) 원격 스토리지에 업로드 (S3, Google Cloud Storage 등)
# aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.gz" s3://my-bucket/backups/
# rclone copy "$BACKUP_DIR/${BACKUP_NAME}.gz" gdrive:backups/

exit 0
