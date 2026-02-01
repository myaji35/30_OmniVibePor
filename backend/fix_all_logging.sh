#!/bin/bash

# Fix all logging imports

files=(
"app/api/v1/audio.py"
"app/api/v1/performance.py"
"app/api/v1/thumbnail_learner.py"
"app/api/v1/voice.py"
"app/services/audio_correction_loop.py"
"app/services/content_performance_tracker.py"
"app/services/embedding_visualizer.py"
"app/services/neo4j_client.py"
"app/services/pdf_to_slides_service.py"
"app/services/stt_service.py"
"app/services/tts_service.py"
"app/services/video_editor_service.py"
"app/services/voice_cloning_service.py"
"app/services/youtube_thumbnail_learner.py"
"app/tasks/audio_tasks.py"
"app/tasks/celery_app.py"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    # Check if file has logging.getLogger
    if grep -q "logging.getLogger" "$file"; then
      # Check if import logging exists
      if ! grep -q "^import logging" "$file"; then
        echo "Adding 'import logging' to $file"
        # Add import logging at the beginning (after docstring if exists)
        if grep -q "^\"\"\"" "$file"; then
          # Has docstring, add after it
          sed -i '' '/^"""$/a\
import logging
' "$file"
        else
          # No docstring, add at the very beginning
          sed -i '' '1i\
import logging
' "$file"
        fi
      else
        echo "  $file already has logging import"
      fi
    fi
  fi
done

echo "Done!"
