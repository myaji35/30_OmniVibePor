#!/bin/bash

# Content Save/Load E2E Test Script
# Tests that generated scripts are saved to DB and can be reloaded

echo "================================"
echo "  Content Save/Load E2E Test"
echo "================================"
echo ""

BASE_URL="http://localhost:3020"
CONTENT_ID=1

echo "[TEST 1] First Generation - Should create new script via Anthropic API"
echo "-----------------------------------------------------------------------"
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/writer-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": '"${CONTENT_ID}"',
    "campaign_name": "테스트 캠페인",
    "topic": "AI 기술의 발전",
    "platform": "YouTube",
    "target_duration": 60,
    "regenerate": false
  }')

echo "$RESPONSE" | jq -r '.success, .source, .cached'

if echo "$RESPONSE" | jq -e '.success == true and .source == "generated" and .cached == null' > /dev/null; then
  echo "✓ PASSED - New script generated via Anthropic API"
else
  echo "✗ FAILED - Expected new generation"
  exit 1
fi

GENERATED_SCRIPT=$(echo "$RESPONSE" | jq -r '.script')
echo "Generated script preview: ${GENERATED_SCRIPT:0:50}..."
echo ""

sleep 2

echo "[TEST 2] Second Load - Should load from database (cached)"
echo "-----------------------------------------------------------------------"
RESPONSE2=$(curl -s -X POST "${BASE_URL}/api/writer-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": '"${CONTENT_ID}"',
    "campaign_name": "테스트 캠페인",
    "topic": "AI 기술의 발전",
    "platform": "YouTube",
    "target_duration": 60,
    "regenerate": false
  }')

echo "$RESPONSE2" | jq -r '.success, .source, .cached'

if echo "$RESPONSE2" | jq -e '.success == true and .source == "database" and .cached == true' > /dev/null; then
  echo "✓ PASSED - Script loaded from database"
else
  echo "✗ FAILED - Expected cached load"
  exit 1
fi

CACHED_SCRIPT=$(echo "$RESPONSE2" | jq -r '.script')
echo "Cached script preview: ${CACHED_SCRIPT:0:50}..."
echo ""

echo "[TEST 3] Content Verification - Scripts should match"
echo "-----------------------------------------------------------------------"
if [ "$GENERATED_SCRIPT" == "$CACHED_SCRIPT" ]; then
  echo "✓ PASSED - Scripts match perfectly"
else
  echo "✗ FAILED - Scripts don't match"
  echo "Generated: ${GENERATED_SCRIPT:0:100}"
  echo "Cached: ${CACHED_SCRIPT:0:100}"
  exit 1
fi
echo ""

echo "[TEST 4] Force Regenerate - Should create new script"
echo "-----------------------------------------------------------------------"
RESPONSE3=$(curl -s -X POST "${BASE_URL}/api/writer-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": '"${CONTENT_ID}"',
    "campaign_name": "테스트 캠페인",
    "topic": "AI 기술의 발전",
    "platform": "YouTube",
    "target_duration": 60,
    "regenerate": true
  }')

echo "$RESPONSE3" | jq -r '.success, .source, .cached'

if echo "$RESPONSE3" | jq -e '.success == true and .source == "generated"' > /dev/null; then
  echo "✓ PASSED - New script generated when regenerate=true"
else
  echo "✗ FAILED - Expected regeneration"
  exit 1
fi
echo ""

echo "================================"
echo "  Test Results Summary"
echo "================================"
echo "Total Tests: 4"
echo "Passed: 4"
echo "Failed: 0"
echo ""
echo "🎉 All tests passed!"
echo ""
echo "📝 Summary:"
echo "  - First call generates new script via Anthropic API"
echo "  - Second call loads from database (cached)"
echo "  - Content matches between calls"
echo "  - Regenerate flag forces new generation"
