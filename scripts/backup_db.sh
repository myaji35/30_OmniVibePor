#!/bin/bash

# OmniVibe Pro - SQLite3 DB 자동 백업 스크립트
# 매일 3시에 자동 실행하도록 cron 설정 권장
# Usage: ./scripts/backup_db.sh

set -e

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="$PROJECT_ROOT/frontend/data/omnivibe.db"
BACKUP_DIR="$PROJECT_ROOT/frontend/data/backups"

# 타임스탬프 설정 (macOS 호환)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/omnivibe_$TIMESTAMP.db"

# 디렉토리 존재 여부 확인
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "📁 백업 디렉토리 생성: $BACKUP_DIR"
fi

# DB 파일 존재 여부 확인
if [ ! -f "$DB_PATH" ]; then
    echo "❌ 오류: DB 파일을 찾을 수 없습니다 - $DB_PATH"
    exit 1
fi

# 백업 실행
echo "⏳ 백업 시작: $(date '+%Y-%m-%d %H:%M:%S')"

cp "$DB_PATH" "$BACKUP_FILE"

if [ -f "$BACKUP_FILE" ]; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ 백업 완료: omnivibe_$TIMESTAMP.db ($FILE_SIZE)"
else
    echo "❌ 백업 실패"
    exit 1
fi

# 7일 이상 된 백업 삭제
echo "🧹 오래된 백업 정리 중..."
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "omnivibe_*.db" -type f -mtime +7 2>/dev/null | wc -l)

if [ "$OLD_BACKUPS" -gt 0 ]; then
    find "$BACKUP_DIR" -name "omnivibe_*.db" -type f -mtime +7 -delete
    echo "✅ $OLD_BACKUPS개의 오래된 백업 삭제 완료"
fi

# 현재 백업 파일 목록 출력
echo ""
echo "📊 백업 현황:"
ls -lh "$BACKUP_DIR"/omnivibe_*.db 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "omnivibe_*.db" -type f | wc -l)
echo "💾 총 백업 개수: $TOTAL_BACKUPS개"
