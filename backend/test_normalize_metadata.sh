#!/bin/bash

# 메타데이터 제거 테스트 스크립트

BASE_URL="http://localhost:8000"

echo "========================================="
echo "Text Normalizer 메타데이터 제거 테스트"
echo "========================================="
echo ""

# 테스트 케이스 1: 마크다운 헤더 및 메타데이터 포함 텍스트
echo "테스트 1: 마크다운 헤더 및 메타데이터 제거"
echo "-----------------------------------------"

curl -X POST "${BASE_URL}/api/v1/audio/normalize-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "### 훅 (첫 3초)\n여러분, 눈이 침침해서 스마트폰 글씨가 안 보인다고 포기하셨나요?\n\n### 본문\n이제 iPhone 저시력자 모드로 세상이 달라집니다.\n\n### CTA\n지금 바로 설정해보세요!\n\n--- 예상 영상 길이: 2분 30초\n--- 플랫폼: 유튜브 쇼츠"
  }' | jq '.'

echo ""
echo ""

# 테스트 케이스 2: 숫자 포함 텍스트 (메타데이터 없음)
echo "테스트 2: 숫자 정규화 (메타데이터 없음)"
echo "-----------------------------------------"

curl -X POST "${BASE_URL}/api/v1/audio/normalize-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다. 오늘은 95.5% 달성했어요!"
  }' | jq '.'

echo ""
echo ""

# 테스트 케이스 3: 복합 메타데이터 (섹션 마커 + 메타데이터)
echo "테스트 3: 복합 메타데이터 제거"
echo "-----------------------------------------"

curl -X POST "${BASE_URL}/api/v1/audio/normalize-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "훅.\n안녕하세요 여러분!\n\n본문.\n오늘은 2024년 새해 첫날입니다.\n\nCTA.\n지금 바로 시작하세요!\n\n--- 타겟: 시니어층\n--- 길이: 30초"
  }' | jq '.'

echo ""
echo ""

echo "========================================="
echo "테스트 완료"
echo "========================================="
