#!/bin/bash

# VideoRenderer API 테스트 스크립트
# 사용법: ./test_video_api.sh

BASE_URL="http://localhost:8000/api/v1/video"

echo "=========================================="
echo "VideoRenderer API 테스트"
echo "=========================================="

# 1. 헬스 체크
echo ""
echo "1️⃣  헬스 체크..."
curl -s -X GET "${BASE_URL}/health" | jq '.'

# 2. 사용 가능한 플랫폼 조회
echo ""
echo "2️⃣  사용 가능한 플랫폼 조회..."
curl -s -X GET "${BASE_URL}/platforms" | jq '.platforms | keys'

# 3. 사용 가능한 전환 효과 조회 (일부만 표시)
echo ""
echo "3️⃣  사용 가능한 전환 효과 조회 (일부만 표시)..."
curl -s -X GET "${BASE_URL}/transitions" | jq '.transitions | to_entries | .[0:5] | from_entries'
curl -s -X GET "${BASE_URL}/transitions" | jq -r '"총 \(.total)가지 전환 효과 지원"'

# 4. 자막 스타일 조회
echo ""
echo "4️⃣  사용 가능한 자막 스타일 조회..."
curl -s -X GET "${BASE_URL}/subtitle-styles" | jq '.styles | keys'

echo ""
echo "=========================================="
echo "✅ 기본 정보 조회 완료"
echo "=========================================="
echo ""
echo "실제 렌더링 테스트를 위해서는 다음을 준비하세요:"
echo "  1. 영상 클립 파일들"
echo "  2. 오디오 파일 (나레이션)"
echo "  3. 자막 파일 (.srt)"
echo ""
echo "렌더링 예시:"
echo "curl -X POST \"${BASE_URL}/render\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"video_clips\": [\"./outputs/videos/clip1.mp4\", \"./outputs/videos/clip2.mp4\"],"
echo "    \"audio_path\": \"./outputs/audio/narration.mp3\","
echo "    \"transitions\": [\"fade\"],"
echo "    \"platform\": \"youtube\""
echo "  }'"
echo ""
