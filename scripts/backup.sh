#!/bin/bash
# ============================================================
# OmniVibe Pro — 자동 백업 스크립트
# 실행: ./scripts/backup.sh
# cron 등록 예시: 0 3 * * * /path/to/scripts/backup.sh >> /var/log/omnivibe_backup.log 2>&1
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/.backups}"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_PREFIX="[BACKUP $DATE]"

echo "$LOG_PREFIX 🚀 OmniVibe Pro 백업 시작"

mkdir -p "$BACKUP_DIR/sqlite" "$BACKUP_DIR/neo4j" "$BACKUP_DIR/logs"

# ── 1. SQLite 백업 ────────────────────────────────────────────
SQLITE_SRC="$PROJECT_ROOT/backend/omni_db.sqlite"
SQLITE_DEST="$BACKUP_DIR/sqlite/omni_db_${DATE}.sqlite"

if [ -f "$SQLITE_SRC" ]; then
  sqlite3 "$SQLITE_SRC" ".backup '$SQLITE_DEST'"
  gzip "$SQLITE_DEST"
  echo "$LOG_PREFIX ✅ SQLite 백업 완료: ${SQLITE_DEST}.gz"
else
  echo "$LOG_PREFIX ⚠️  SQLite 파일 없음: $SQLITE_SRC"
fi

# 30일 이상 된 SQLite 백업 삭제
find "$BACKUP_DIR/sqlite" -name "*.gz" -mtime +30 -delete
echo "$LOG_PREFIX 🧹 30일 이상 SQLite 백업 정리 완료"

# ── 2. Neo4j 백업 (Docker 컨테이너 실행 중일 때만) ──────────────
NEO4J_CONTAINER="${NEO4J_CONTAINER:-omnivibe-neo4j}"
NEO4J_DEST="$BACKUP_DIR/neo4j/neo4j_${DATE}.dump"

if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${NEO4J_CONTAINER}$"; then
  docker exec "$NEO4J_CONTAINER" \
    neo4j-admin database dump neo4j --to-path=/var/lib/neo4j/data/dumps/ 2>/dev/null || true

  DUMP_SRC=$(docker exec "$NEO4J_CONTAINER" \
    find /var/lib/neo4j/data/dumps -name "*.dump" -newer /var/lib/neo4j/data/dumps 2>/dev/null | head -1)

  if [ -n "$DUMP_SRC" ]; then
    docker cp "${NEO4J_CONTAINER}:${DUMP_SRC}" "$NEO4J_DEST"
    gzip "$NEO4J_DEST"
    echo "$LOG_PREFIX ✅ Neo4j 백업 완료: ${NEO4J_DEST}.gz"
  fi

  # 90일 이상 된 Neo4j 백업 삭제
  find "$BACKUP_DIR/neo4j" -name "*.gz" -mtime +90 -delete
else
  echo "$LOG_PREFIX ⚠️  Neo4j 컨테이너 미실행, 백업 건너뜀"
fi

# ── 3. 로그 파일 압축 보관 ────────────────────────────────────
LOG_SRC="$PROJECT_ROOT/backend/logs"
if [ -d "$LOG_SRC" ]; then
  tar -czf "$BACKUP_DIR/logs/logs_${DATE}.tar.gz" -C "$LOG_SRC" . 2>/dev/null || true
  echo "$LOG_PREFIX ✅ 로그 백업 완료"
  # 7일 이상 된 로그 백업 삭제
  find "$BACKUP_DIR/logs" -name "*.tar.gz" -mtime +7 -delete
fi

# ── 4. 디스크 사용량 경고 ─────────────────────────────────────
OUTPUTS_DIR="$PROJECT_ROOT/backend/outputs"
if [ -d "$OUTPUTS_DIR" ]; then
  USAGE=$(du -sm "$OUTPUTS_DIR" 2>/dev/null | cut -f1)
  if [ "$USAGE" -gt 10240 ]; then   # 10GB 초과 시 경고
    echo "$LOG_PREFIX ⚠️  outputs/ 디스크 사용량 경고: ${USAGE}MB"
  else
    echo "$LOG_PREFIX 📦 outputs/ 디스크 사용량: ${USAGE}MB (정상)"
  fi
fi

# ── 5. 완료 요약 ──────────────────────────────────────────────
echo "$LOG_PREFIX ✅ 백업 완료"
echo "$LOG_PREFIX 📁 백업 위치: $BACKUP_DIR"
ls -lh "$BACKUP_DIR/sqlite/" 2>/dev/null | tail -3
