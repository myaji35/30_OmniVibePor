#!/bin/bash

# Storyboard API 테스트 스크립트

echo "=========================================="
echo "Storyboard API Test"
echo "=========================================="

BASE_URL="http://localhost:8000/api/v1"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Health Check
echo -e "\n${YELLOW}1. Health Check${NC}"
curl -s -X GET "${BASE_URL}/storyboard/health" | python3 -m json.tool

# 2. Storyboard 생성 (동기 모드)
echo -e "\n${YELLOW}2. Storyboard Generation (Sync Mode)${NC}"
curl -s -X POST "${BASE_URL}/storyboard/campaigns/1/content/1/generate?async_mode=false" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "여러분, 오늘은 AI에 대해 알아봅시다. AI는 우리의 일상을 변화시키고 있습니다. 자동화된 시스템부터 창의적인 작업까지, AI의 영향력은 점점 커지고 있습니다. 우리는 이 변화에 어떻게 대응해야 할까요? 함께 고민해봅시다.",
    "campaign_concept": {
      "gender": "female",
      "tone": "professional",
      "style": "modern",
      "platform": "YouTube"
    },
    "target_duration": 30
  }' | python3 -m json.tool

# 3. Storyboard 생성 (비동기 모드)
echo -e "\n${YELLOW}3. Storyboard Generation (Async Mode)${NC}"
TASK_RESPONSE=$(curl -s -X POST "${BASE_URL}/storyboard/campaigns/2/content/2/generate?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "안녕하세요, 여러분! 오늘은 특별한 이야기를 준비했습니다. 혁신적인 기술이 우리의 미래를 어떻게 바꿀지 함께 살펴보겠습니다.",
    "campaign_concept": {
      "gender": "male",
      "tone": "energetic",
      "style": "creative",
      "platform": "Instagram"
    },
    "target_duration": 60
  }')

echo "$TASK_RESPONSE" | python3 -m json.tool

# Task ID 추출
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', '').split('ID: ')[-1].split('.')[0] if 'error' in data else '')")

if [ -n "$TASK_ID" ]; then
  echo -e "\n${GREEN}Task ID: $TASK_ID${NC}"

  # 4. Task 상태 조회
  echo -e "\n${YELLOW}4. Task Status Check${NC}"
  sleep 2  # 작업 시작 대기
  curl -s -X GET "${BASE_URL}/storyboard/task/${TASK_ID}" | python3 -m json.tool
fi

# 5. Storyboard 블록 조회
echo -e "\n${YELLOW}5. Get Storyboard Blocks${NC}"
curl -s -X GET "${BASE_URL}/storyboard/campaigns/1/content/1/blocks" | python3 -m json.tool

echo -e "\n${GREEN}=========================================="
echo "Test Complete"
echo "==========================================${NC}"
