#!/bin/bash

echo "========================================="
echo "커스텀 프리셋 API 테스트"
echo "========================================="
echo ""

BASE_URL="http://localhost:8000/api/v1"
USER_ID="test_user_$(date +%s)"

echo "1. 커스텀 프리셋 생성 (POST /presets/custom)"
echo "-------------------------------------------"
CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/presets/custom?user_id=${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트 프리셋",
    "description": "자동 테스트용 프리셋입니다",
    "is_favorite": true
  }')

echo "$CREATE_RESPONSE" | python3 -m json.tool
PRESET_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('preset_id', ''))" 2>/dev/null)
echo ""
echo "생성된 preset_id: $PRESET_ID"
echo ""

if [ -z "$PRESET_ID" ]; then
  echo "❌ 프리셋 생성 실패"
  exit 1
fi

echo "✓ 프리셋 생성 성공"
echo ""

echo "2. 커스텀 프리셋 목록 조회 (GET /presets/custom)"
echo "-------------------------------------------"
curl -s "${BASE_URL}/presets/custom?user_id=${USER_ID}" | python3 -m json.tool
echo ""
echo "✓ 프리셋 목록 조회 성공"
echo ""

echo "3. 커스텀 프리셋 상세 조회 (GET /presets/custom/{preset_id})"
echo "-------------------------------------------"
curl -s "${BASE_URL}/presets/custom/${PRESET_ID}" | python3 -m json.tool
echo ""
echo "✓ 프리셋 상세 조회 성공"
echo ""

echo "4. 커스텀 프리셋 수정 (PATCH /presets/custom/{preset_id})"
echo "-------------------------------------------"
curl -s -X PATCH "${BASE_URL}/presets/custom/${PRESET_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "수정된 프리셋",
    "is_favorite": false
  }' | python3 -m json.tool
echo ""
echo "✓ 프리셋 수정 성공"
echo ""

echo "5. 커스텀 프리셋 삭제 (DELETE /presets/custom/{preset_id})"
echo "-------------------------------------------"
curl -s -X DELETE "${BASE_URL}/presets/custom/${PRESET_ID}" | python3 -m json.tool
echo ""
echo "✓ 프리셋 삭제 성공"
echo ""

echo "========================================="
echo "✅ 모든 테스트 통과"
echo "========================================="
