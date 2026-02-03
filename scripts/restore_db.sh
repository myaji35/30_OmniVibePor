#!/bin/bash

# OmniVibe Pro - SQLite3 DB 복구 스크립트
# 특정 백업에서 데이터베이스를 복구합니다
# Usage: ./scripts/restore_db.sh <backup_filename>
# 예시: ./scripts/restore_db.sh omnivibe_20260203_030000.db

set -e

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="$PROJECT_ROOT/frontend/data/omnivibe.db"
BACKUP_DIR="$PROJECT_ROOT/frontend/data/backups"

# 사용법 확인
if [ -z "$1" ]; then
    echo "❌ 사용법: ./scripts/restore_db.sh <backup_filename>"
    echo ""
    echo "📋 사용 가능한 백업 파일:"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR"/omnivibe_*.db 2>/dev/null)" ]; then
        ls -lh "$BACKUP_DIR"/omnivibe_*.db | awk '{print "  " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}'
    else
        echo "  (백업 파일이 없습니다)"
    fi
    exit 1
fi

BACKUP_FILE="$BACKUP_DIR/$1"

# 백업 파일 존재 여부 확인
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 오류: 백업 파일을 찾을 수 없습니다"
    echo "경로: $BACKUP_FILE"
    echo ""
    echo "📋 사용 가능한 백업 파일:"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR"/omnivibe_*.db 2>/dev/null)" ]; then
        ls -lh "$BACKUP_DIR"/omnivibe_*.db | awk '{print "  " $9}'
    else
        echo "  (백업 파일이 없습니다)"
    fi
    exit 1
fi

# 안전 확인
echo "⚠️  경고: 현재 데이터베이스가 새 백업으로 덮어쓰기됩니다!"
echo ""
echo "📌 복구할 파일: $1"
echo "📌 원본 DB: $DB_PATH"
echo ""
read -p "정말 진행하시겠습니까? (y/N): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 복구 취소됨"
    exit 0
fi

# 현재 DB의 안전 백업 생성
SAFETY_BACKUP="$PROJECT_ROOT/frontend/data/omnivibe_before_restore_$(date +%Y%m%d_%H%M%S).db"
echo "🛡️  안전 백업 생성 중..."
cp "$DB_PATH" "$SAFETY_BACKUP"
echo "✅ 안전 백업 생성: $(basename "$SAFETY_BACKUP")"

# DB 복구 실행
echo ""
echo "⏳ 복구 시작: $(date '+%Y-%m-%d %H:%M:%S')"
cp "$BACKUP_FILE" "$DB_PATH"
echo "✅ 복구 완료!"

# 복구된 파일 정보 출력
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo ""
echo "📊 복구 결과:"
echo "  파일: $DB_PATH"
echo "  크기: $DB_SIZE"
echo "  시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "💡 팁: 복구에 문제가 있으면 다음 명령어로 되돌릴 수 있습니다:"
echo "  cp \"$SAFETY_BACKUP\" \"$DB_PATH\""
