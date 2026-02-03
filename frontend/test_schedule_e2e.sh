#!/bin/bash

# E2E Test Script for /schedule Page
# Tests all CRUD operations, pagination, filters, and bulk operations

API_BASE="http://localhost:3020/api/sheets-schedule"
PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}  Schedule E2E Test Suite${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

# Test 1: GET - Read all schedules with pagination
echo -e "${YELLOW}[TEST 1]${NC} GET /api/sheets-schedule - Pagination"
RESPONSE=$(curl -s "${API_BASE}?page=1&limit=5")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  COUNT=$(echo $RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
  TOTAL=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ PASSED${NC} - Retrieved $COUNT items (Total: $TOTAL)"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - API returned error"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: GET - Search filter
echo -e "${YELLOW}[TEST 2]${NC} GET /api/sheets-schedule - Search Filter"
RESPONSE=$(curl -s "${API_BASE}?page=1&limit=10&search=%EC%A0%80%EC%8B%9C%EB%A0%A5")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  COUNT=$(echo $RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ PASSED${NC} - Search returned $COUNT results"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Search filter failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: GET - Platform filter
echo -e "${YELLOW}[TEST 3]${NC} GET /api/sheets-schedule - Platform Filter"
RESPONSE=$(curl -s "${API_BASE}?page=1&limit=10&platform=Youtube")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  COUNT=$(echo $RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ PASSED${NC} - Platform filter returned $COUNT Youtube items"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Platform filter failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: GET - Status filter
echo -e "${YELLOW}[TEST 4]${NC} GET /api/sheets-schedule - Status Filter"
RESPONSE=$(curl -s "${API_BASE}?page=1&limit=10&status=draft")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  COUNT=$(echo $RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ PASSED${NC} - Status filter returned $COUNT draft items"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Status filter failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: GET - Combined filters
echo -e "${YELLOW}[TEST 5]${NC} GET /api/sheets-schedule - Combined Filters"
RESPONSE=$(curl -s "${API_BASE}?page=1&limit=10&platform=Youtube&status=draft")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  COUNT=$(echo $RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ PASSED${NC} - Combined filters returned $COUNT items"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Combined filters failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 6: POST - Create new schedule
echo -e "${YELLOW}[TEST 6]${NC} POST /api/sheets-schedule - Create Schedule"
RESPONSE=$(curl -s -X POST "${API_BASE}" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "topic": "E2E Test Topic",
    "subtitle": "E2E Test Subtitle",
    "platform": "Youtube",
    "publish_date": "2026-12-31",
    "status": "draft",
    "keywords": "test, e2e, automation"
  }')

SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)
if [ $SUCCESS -gt 0 ]; then
  NEW_ID=$(echo $RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)
  echo -e "${GREEN}✓ PASSED${NC} - Created schedule with ID: $NEW_ID"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Schedule creation failed"
  echo "Response: $RESPONSE"
  FAILED=$((FAILED + 1))
  NEW_ID=""
fi
echo ""

# Test 7: PUT - Update schedule (if creation succeeded)
if [ ! -z "$NEW_ID" ]; then
  echo -e "${YELLOW}[TEST 7]${NC} PUT /api/sheets-schedule - Update Schedule"
  RESPONSE=$(curl -s -X PUT "${API_BASE}" \
    -H "Content-Type: application/json" \
    -d "{
      \"id\": $NEW_ID,
      \"subtitle\": \"E2E Test Subtitle - UPDATED\",
      \"status\": \"scheduled\"
    }")

  SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)
  if [ $SUCCESS -gt 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Updated schedule ID: $NEW_ID"
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ FAILED${NC} - Schedule update failed"
    FAILED=$((FAILED + 1))
  fi
  echo ""
else
  echo -e "${YELLOW}[TEST 7]${NC} PUT /api/sheets-schedule - SKIPPED (no ID from previous test)"
  echo ""
fi

# Test 8: DELETE - Delete schedule (if creation succeeded)
if [ ! -z "$NEW_ID" ]; then
  echo -e "${YELLOW}[TEST 8]${NC} DELETE /api/sheets-schedule - Delete Schedule"
  RESPONSE=$(curl -s -X DELETE "${API_BASE}?id=$NEW_ID")

  SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)
  if [ $SUCCESS -gt 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Deleted schedule ID: $NEW_ID"
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ FAILED${NC} - Schedule deletion failed"
    FAILED=$((FAILED + 1))
  fi
  echo ""
else
  echo -e "${YELLOW}[TEST 8]${NC} DELETE /api/sheets-schedule - SKIPPED (no ID from previous test)"
  echo ""
fi

# Test 9: POST - Validation (Missing required fields)
echo -e "${YELLOW}[TEST 9]${NC} POST /api/sheets-schedule - Validation Test"
RESPONSE=$(curl -s -X POST "${API_BASE}" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Missing Campaign ID"
  }')

ERROR=$(echo $RESPONSE | grep -o '"success":false' | wc -l)
if [ $ERROR -gt 0 ]; then
  echo -e "${GREEN}✓ PASSED${NC} - Validation correctly rejected incomplete data"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Validation should have rejected incomplete data"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 10: POST - Date validation (past date)
echo -e "${YELLOW}[TEST 10]${NC} POST /api/sheets-schedule - Past Date Validation"
RESPONSE=$(curl -s -X POST "${API_BASE}" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "topic": "Past Date Test",
    "subtitle": "Should Fail",
    "platform": "Youtube",
    "publish_date": "2020-01-01",
    "status": "draft"
  }')

ERROR=$(echo $RESPONSE | grep -o '"success":false' | wc -l)
if [ $ERROR -gt 0 ]; then
  echo -e "${GREEN}✓ PASSED${NC} - Date validation correctly rejected past date"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}✗ FAILED${NC} - Date validation should have rejected past date"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 11: GET - Pagination (page 2)
echo -e "${YELLOW}[TEST 11]${NC} GET /api/sheets-schedule - Page 2 Test"
RESPONSE=$(curl -s "${API_BASE}?page=2&limit=5")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  PAGE=$(echo $RESPONSE | grep -o '"page":2' | wc -l)
  if [ $PAGE -gt 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Page 2 retrieved successfully"
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ FAILED${NC} - Page number mismatch"
    FAILED=$((FAILED + 1))
  fi
else
  echo -e "${RED}✗ FAILED${NC} - Pagination failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 12: GET - Items per page (20)
echo -e "${YELLOW}[TEST 12]${NC} GET /api/sheets-schedule - Items Per Page Test"
RESPONSE=$(curl -s "${API_BASE}?page=1&limit=20")
SUCCESS=$(echo $RESPONSE | grep -o '"success":true' | wc -l)

if [ $SUCCESS -gt 0 ]; then
  LIMIT=$(echo $RESPONSE | grep -o '"limit":20' | wc -l)
  if [ $LIMIT -gt 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC} - Items per page set to 20"
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ FAILED${NC} - Items per page mismatch"
    FAILED=$((FAILED + 1))
  fi
else
  echo -e "${RED}✗ FAILED${NC} - Items per page test failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}  Test Results Summary${NC}"
echo -e "${YELLOW}================================${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
  echo -e "\n${GREEN}🎉 All tests passed!${NC}"
  exit 0
else
  echo -e "\n${RED}⚠️  Some tests failed${NC}"
  exit 1
fi
