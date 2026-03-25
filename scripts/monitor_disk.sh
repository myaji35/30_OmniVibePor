#!/bin/bash
# ============================================================
# OmniVibe Pro — 디스크 사용량 모니터링 (O-5)
# 실행: ./scripts/monitor_disk.sh
# cron 등록 예시: */30 * * * * /path/to/scripts/monitor_disk.sh >> /var/log/omnivibe_disk.log 2>&1
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
LOG_PREFIX="[DISK $DATE]"

# ── 임계값 설정 ────────────────────────────────────────────────
WARN_MB=10240    # 10GB 경고
CRIT_MB=20480    # 20GB 위험
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"   # 환경변수에서 읽음

# ── 모니터링 대상 디렉토리 ────────────────────────────────────
declare -A DIRS=(
  ["outputs"]="$PROJECT_ROOT/backend/outputs"
  ["generated_audio"]="$PROJECT_ROOT/backend/generated_audio"
  ["fallback"]="$PROJECT_ROOT/backend/outputs/fallback"
  ["backups"]="$PROJECT_ROOT/.backups"
  ["logs"]="$PROJECT_ROOT/backend/logs"
)

_slack() {
  local msg="$1"
  [ -z "$SLACK_WEBHOOK" ] && return
  curl -s -X POST "$SLACK_WEBHOOK" \
    -H 'Content-type: application/json' \
    --data "{\"text\":\"$msg\"}" > /dev/null 2>&1 || true
}

_check_dir() {
  local name="$1"
  local path="$2"

  [ -d "$path" ] || return 0

  local mb
  mb=$(du -sm "$path" 2>/dev/null | cut -f1)

  echo "$LOG_PREFIX [$name] ${mb}MB ($path)"

  if [ "$mb" -ge "$CRIT_MB" ]; then
    echo "$LOG_PREFIX 🚨 CRITICAL: $name ${mb}MB >= ${CRIT_MB}MB"
    _slack ":rotating_light: *OmniVibe 디스크 위험* \`$name\` = ${mb}MB (임계값: ${CRIT_MB}MB)"

  elif [ "$mb" -ge "$WARN_MB" ]; then
    echo "$LOG_PREFIX ⚠️  WARNING: $name ${mb}MB >= ${WARN_MB}MB"
    _slack ":warning: *OmniVibe 디스크 경고* \`$name\` = ${mb}MB (임계값: ${WARN_MB}MB)"
  fi
}

# ── 각 디렉토리 체크 ──────────────────────────────────────────
for name in "${!DIRS[@]}"; do
  _check_dir "$name" "${DIRS[$name]}"
done

# ── 전체 디스크 사용률 ────────────────────────────────────────
DISK_PERCENT=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | tr -d '%')
echo "$LOG_PREFIX [disk_usage] ${DISK_PERCENT}%"

if [ "$DISK_PERCENT" -ge 90 ]; then
  echo "$LOG_PREFIX 🚨 CRITICAL: 전체 디스크 사용률 ${DISK_PERCENT}%"
  _slack ":rotating_light: *OmniVibe 전체 디스크 위험* ${DISK_PERCENT}% 사용 중"
elif [ "$DISK_PERCENT" -ge 80 ]; then
  echo "$LOG_PREFIX ⚠️  WARNING: 전체 디스크 사용률 ${DISK_PERCENT}%"
  _slack ":warning: *OmniVibe 전체 디스크 경고* ${DISK_PERCENT}% 사용 중"
fi

# ── 오래된 임시 파일 자동 정리 ───────────────────────────────
CLEANED=0
while IFS= read -r -d '' f; do
  rm -f "$f" && CLEANED=$((CLEANED+1))
done < <(find "$PROJECT_ROOT/backend/outputs" \
  -name "*.tmp" -o -name "preview_*.mp4" \
  -mtime +3 -print0 2>/dev/null)

[ "$CLEANED" -gt 0 ] && echo "$LOG_PREFIX 🧹 임시 파일 ${CLEANED}개 삭제"

echo "$LOG_PREFIX ✅ 디스크 모니터링 완료"
