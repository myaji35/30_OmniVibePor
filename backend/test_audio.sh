#!/bin/bash

echo "⏰ 시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

START=$(date +%s)

# API 호출
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d @request.json)

echo "$RESPONSE"
TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

echo ""
echo "📝 작업 ID: $TASK_ID"
echo "⏱️  진행 상황 모니터링 중..."
echo ""

# 상태 체크
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/v1/audio/status/$TASK_ID" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  echo "  상태: $STATUS"

  if [ "$STATUS" = "SUCCESS" ] || [ "$STATUS" = "FAILURE" ]; then
    break
  fi

  sleep 2
done

END=$(date +%s)
ELAPSED=$((END - START))

echo ""
echo "⏰ 종료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "⏱️  총 소요 시간: ${ELAPSED}초 ($((ELAPSED / 60))분 $((ELAPSED % 60))초)"

if [ "$STATUS" = "SUCCESS" ]; then
  echo ""
  echo "✅ 오디오 생성 성공!"
  curl -s "http://localhost:8000/api/v1/audio/status/$TASK_ID" | python3 -m json.tool
fi
