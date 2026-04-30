#!/usr/bin/env bash
# ISS-162 — Phase B Gate G3-a smoke render
# 작업 디렉터리: frontend/
# 사용법: bash remotion/scripts/smoke-render.sh [OUT_DIR]
set -euo pipefail

OUT_DIR="${1:-/tmp/omnivibe-smoke}"
mkdir -p "$OUT_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_PATH="$OUT_DIR/smoke-test-${TIMESTAMP}.mp4"

# frontend/ 기준 실행
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$FRONTEND_DIR"

echo "[smoke] Remotion render → $OUT_PATH"
echo "[smoke] cwd = $FRONTEND_DIR"

npx remotion render remotion/index.ts SmokeTest "$OUT_PATH" \
  --fps 30 \
  --image-format jpeg \
  --jpeg-quality 80 \
  --concurrency 2 \
  --log error

if [ ! -s "$OUT_PATH" ]; then
  echo "[FAIL] 출력 파일 0바이트 또는 미생성: $OUT_PATH"
  exit 1
fi

FILESIZE=$(stat -f%z "$OUT_PATH" 2>/dev/null || stat -c%s "$OUT_PATH")
echo "[smoke] 렌더 완료. 크기=${FILESIZE} bytes"
echo "[smoke] 경로: $OUT_PATH"
echo "$OUT_PATH"
