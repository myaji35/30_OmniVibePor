#!/bin/bash
# Zero-Fault Audio API 통합 테스트 스크립트

set -e

BASE_URL="http://localhost:8000"
API_URL="${BASE_URL}/api/v1"

echo "🚀 OmniVibe Pro - API 통합 테스트 시작"
echo "=========================================="

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 결과 카운터
PASSED=0
FAILED=0

# 테스트 함수
test_endpoint() {
    local test_name=$1
    local endpoint=$2
    local method=${3:-GET}
    local data=${4:-}

    echo -e "\n${YELLOW}Testing:${NC} $test_name"
    echo "  Endpoint: $method $endpoint"

    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        echo "  Response: $(echo $body | jq -c '.' 2>/dev/null || echo $body | head -c 100)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "  ${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "  Error: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. 헬스체크
echo -e "\n${YELLOW}=== Phase 1: Health Checks ===${NC}"
test_endpoint "Root Health Check" "$BASE_URL/"
test_endpoint "API Health Check" "$BASE_URL/health"

# 2. 음성 목록 조회
echo -e "\n${YELLOW}=== Phase 2: Audio Service ===${NC}"
test_endpoint "List Available Voices" "$API_URL/audio/voices"
test_endpoint "Check API Usage" "$API_URL/audio/usage"

# 3. 오디오 생성 (실제 API 호출 - 주의!)
echo -e "\n${YELLOW}=== Phase 3: Zero-Fault Audio Generation ===${NC}"

# 테스트용 짧은 텍스트 (비용 절감)
TEST_TEXT="안녕하세요 테스트입니다"

echo -e "${YELLOW}⚠️  주의: 실제 ElevenLabs API를 호출합니다 (비용 발생 가능)${NC}"
echo "계속하려면 Enter를 누르세요 (취소하려면 Ctrl+C)..."
read -r

GENERATE_DATA=$(cat <<EOF
{
  "text": "$TEST_TEXT",
  "language": "ko",
  "user_id": "test_user",
  "accuracy_threshold": 0.95,
  "max_attempts": 3
}
EOF
)

if test_endpoint "Generate Verified Audio" "$API_URL/audio/generate" "POST" "$GENERATE_DATA"; then
    TASK_ID=$(echo "$body" | jq -r '.task_id')
    echo -e "  Task ID: ${GREEN}$TASK_ID${NC}"

    # 4. 작업 상태 확인 (폴링)
    echo -e "\n${YELLOW}=== Phase 4: Task Status Monitoring ===${NC}"

    MAX_ATTEMPTS=30
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))

        echo -e "  ${YELLOW}[$ATTEMPT/$MAX_ATTEMPTS]${NC} Checking task status..."

        status_response=$(curl -s "$API_URL/audio/status/$TASK_ID")
        task_status=$(echo "$status_response" | jq -r '.status')

        echo "    Status: $task_status"

        if [ "$task_status" == "SUCCESS" ]; then
            echo -e "  ${GREEN}✓ Task completed successfully!${NC}"

            # 결과 출력
            final_similarity=$(echo "$status_response" | jq -r '.result.final_similarity')
            attempts=$(echo "$status_response" | jq -r '.result.attempts')
            audio_path=$(echo "$status_response" | jq -r '.result.audio_path')

            echo "    Final Similarity: $final_similarity"
            echo "    Attempts: $attempts"
            echo "    Audio Path: $audio_path"

            PASSED=$((PASSED + 1))

            # 5. 다운로드 테스트
            echo -e "\n${YELLOW}=== Phase 5: Audio Download ===${NC}"

            download_file="./test_verified_audio.mp3"
            if curl -s "$API_URL/audio/download/$TASK_ID" -o "$download_file"; then
                file_size=$(wc -c < "$download_file")
                if [ "$file_size" -gt 0 ]; then
                    echo -e "  ${GREEN}✓ Audio downloaded successfully${NC}"
                    echo "    File: $download_file"
                    echo "    Size: $file_size bytes"
                    PASSED=$((PASSED + 1))
                else
                    echo -e "  ${RED}✗ Downloaded file is empty${NC}"
                    FAILED=$((FAILED + 1))
                fi
            else
                echo -e "  ${RED}✗ Download failed${NC}"
                FAILED=$((FAILED + 1))
            fi

            break
        elif [ "$task_status" == "FAILURE" ]; then
            echo -e "  ${RED}✗ Task failed${NC}"
            echo "    Error: $(echo "$status_response" | jq -r '.error')"
            FAILED=$((FAILED + 1))
            break
        elif [ "$task_status" == "PENDING" ] || [ "$task_status" == "STARTED" ]; then
            # 계속 대기
            continue
        else
            echo -e "  ${YELLOW}⚠ Unknown status: $task_status${NC}"
        fi
    done

    if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        echo -e "  ${RED}✗ Timeout waiting for task completion${NC}"
        FAILED=$((FAILED + 1))
    fi
fi

# 6. 썸네일 학습 API (Phase 0)
echo -e "\n${YELLOW}=== Phase 6: Thumbnail Learning API ===${NC}"
test_endpoint "Search Similar Thumbnails" "$API_URL/thumbnails/search?query=AI+트렌드&top_k=5"

# 7. 성과 추적 API (Phase 0)
echo -e "\n${YELLOW}=== Phase 7: Performance Tracking API ===${NC}"
test_endpoint "Get User Insights" "$API_URL/performance/insights/test_user"

# 최종 결과
echo -e "\n=========================================="
echo -e "${YELLOW}테스트 완료!${NC}"
echo -e "  ${GREEN}✓ Passed:${NC} $PASSED"
echo -e "  ${RED}✗ Failed:${NC} $FAILED"
echo -e "  Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed.${NC}"
    exit 1
fi
