#!/bin/bash

# 전체 워크플로우 E2E 테스트 (Script → Audio)
# 스크립트 생성부터 오디오 생성까지 전체 파이프라인 테스트

echo "========================================="
echo "  Full Workflow E2E Test"
echo "  Script Generation → Audio Generation"
echo "========================================="
echo ""

BASE_URL_FRONTEND="http://localhost:3020"
BASE_URL_BACKEND="http://localhost:8000"
CONTENT_ID=1001

echo "[STEP 1] 스크립트 생성"
echo "---------------------------------------"
SCRIPT_RES=$(curl -s -X POST "${BASE_URL_FRONTEND}/api/writer-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": '${CONTENT_ID}',
    "campaign_name": "E2E 테스트 캠페인",
    "topic": "AI 음성 합성 기술",
    "platform": "YouTube",
    "target_duration": 30,
    "regenerate": false
  }')

echo "$SCRIPT_RES" | jq -r '.success, .source'

if echo "$SCRIPT_RES" | jq -e '.success == true' > /dev/null; then
  echo "✅ PASSED - 스크립트 생성 성공"
  SCRIPT=$(echo "$SCRIPT_RES" | jq -r '.script')
  echo "Script preview: ${SCRIPT:0:50}..."
else
  echo "❌ FAILED - 스크립트 생성 실패"
  echo "$SCRIPT_RES" | jq '.'
  exit 1
fi

echo ""
sleep 2

echo "[STEP 2] 오디오 생성"
echo "---------------------------------------"
AUDIO_RES=$(curl -s -X POST "${BASE_URL_BACKEND}/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": $(echo "$SCRIPT" | jq -Rs .),
    \"voice_id\": \"rachel\",
    \"language\": \"ko\",
    \"accuracy_threshold\": 0.95,
    \"max_attempts\": 3
  }")

echo "$AUDIO_RES" | jq -r '.status, .task_id'

if echo "$AUDIO_RES" | jq -e '.task_id' > /dev/null; then
  echo "✅ PASSED - 오디오 생성 작업 시작"
  TASK_ID=$(echo "$AUDIO_RES" | jq -r '.task_id')
  echo "Task ID: $TASK_ID"
else
  echo "❌ FAILED - 오디오 생성 시작 실패"
  echo "$AUDIO_RES" | jq '.'
  exit 1
fi

echo ""
echo "[STEP 3] 오디오 생성 상태 확인 (최대 30초 대기)"
echo "---------------------------------------"

for i in {1..6}; do
  echo "⏳ 상태 확인 중... ($i/6)"
  STATUS_RES=$(curl -s "${BASE_URL_BACKEND}/api/v1/audio/status/${TASK_ID}")

  STATUS=$(echo "$STATUS_RES" | jq -r '.status')

  if [ "$STATUS" = "SUCCESS" ]; then
    echo "✅ PASSED - 오디오 생성 완료"
    AUDIO_PATH=$(echo "$STATUS_RES" | jq -r '.info.result.audio_path')
    SIMILARITY=$(echo "$STATUS_RES" | jq -r '.info.result.final_similarity')
    ATTEMPTS=$(echo "$STATUS_RES" | jq -r '.info.result.attempts')

    echo "Audio file: $AUDIO_PATH"
    echo "Similarity: $SIMILARITY"
    echo "Attempts: $ATTEMPTS"
    break
  elif [ "$STATUS" = "FAILURE" ]; then
    echo "❌ FAILED - 오디오 생성 실패"
    echo "$STATUS_RES" | jq '.info'
    exit 1
  else
    echo "   Status: $STATUS"
    sleep 5
  fi

  if [ $i -eq 6 ]; then
    echo "⚠️  WARNING - 30초 내에 완료되지 않음 (타임아웃)"
    exit 1
  fi
done

echo ""
echo "========================================="
echo "  Test Results Summary"
echo "========================================="
echo "✅ Script Generation: PASSED"
echo "✅ Audio Generation: PASSED"
echo "✅ Full Workflow: PASSED"
echo ""
echo "🎉 All E2E tests passed!"
