#!/bin/bash

# Phase 7 Integration Test Script
# Presentation Mode End-to-End Test

set -e

API_BASE="http://localhost:8123/api/v1"
PROJECT_ID="test-project-001"
PDF_PATH="./test_data/sample_presentation.pdf"

echo "=================================================="
echo "Phase 7 Presentation Mode Integration Test"
echo "=================================================="
echo ""

# Step 1: Health Check
echo "Step 1: Health Check"
curl -s "${API_BASE}/health" | jq '.'
echo ""

# Step 2: Upload PDF
echo "Step 2: Uploading PDF..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  "${API_BASE}/presentations/upload" \
  -F "file=@${PDF_PATH}" \
  -F "project_id=${PROJECT_ID}" \
  -F "dpi=200" \
  -F "lang=kor+eng")

echo "$UPLOAD_RESPONSE" | jq '.'
PRESENTATION_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.presentation_id')
echo "Presentation ID: $PRESENTATION_ID"
echo ""

# Step 3: Generate Script
echo "Step 3: Generating narration script..."
SCRIPT_RESPONSE=$(curl -s -X POST \
  "${API_BASE}/presentations/${PRESENTATION_ID}/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "tone": "professional",
    "target_duration_per_slide": 15.0
  }')

echo "$SCRIPT_RESPONSE" | jq '.'
echo ""

# Step 4: Generate Audio
echo "Step 4: Generating TTS audio..."
AUDIO_RESPONSE=$(curl -s -X POST \
  "${API_BASE}/presentations/${PRESENTATION_ID}/generate-audio" \
  -H "Content-Type: application/json" \
  -d '{
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75
  }')

echo "$AUDIO_RESPONSE" | jq '.'
echo ""

# Step 5: Analyze Timing
echo "Step 5: Analyzing slide timing with Whisper..."
TIMING_RESPONSE=$(curl -s -X POST \
  "${API_BASE}/presentations/${PRESENTATION_ID}/analyze-timing")

echo "$TIMING_RESPONSE" | jq '.'
echo ""

# Step 6: Generate Video
echo "Step 6: Generating presentation video..."
VIDEO_RESPONSE=$(curl -s -X POST \
  "${API_BASE}/presentations/${PRESENTATION_ID}/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "transition_effect": "fade",
    "transition_duration": 0.5,
    "bgm_settings": {
      "enabled": false
    }
  }')

echo "$VIDEO_RESPONSE" | jq '.'
TASK_ID=$(echo "$VIDEO_RESPONSE" | jq -r '.task_id')
echo "Task ID: $TASK_ID"
echo ""

# Step 7: Poll Video Status
echo "Step 7: Polling video generation status..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  STATUS_RESPONSE=$(curl -s "${API_BASE}/presentations/${PRESENTATION_ID}")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')

  echo "  [$RETRY_COUNT] Status: $STATUS"

  if [ "$STATUS" = "VIDEO_READY" ]; then
    echo ""
    echo "✅ Video generation completed!"
    echo "$STATUS_RESPONSE" | jq '.'
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "❌ Video generation failed!"
    echo "$STATUS_RESPONSE" | jq '.error'
    exit 1
  fi

  sleep 3
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo ""
  echo "⏱️ Timeout: Video generation took too long"
  exit 1
fi

echo ""
echo "=================================================="
echo "Integration Test Completed Successfully!"
echo "=================================================="
