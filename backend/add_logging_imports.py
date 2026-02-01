#!/usr/bin/env python3
"""Add logging import to all files that use logging.getLogger"""

import re
from pathlib import Path

files_to_fix = [
    "app/services/audio_correction_loop.py",
    "app/services/content_performance_tracker.py",
    "app/services/embedding_visualizer.py",
    "app/services/neo4j_client.py",
    "app/services/pdf_to_slides_service.py",
    "app/services/stt_service.py",
    "app/services/tts_service.py",
    "app/services/video_editor_service.py",
    "app/services/voice_cloning_service.py",
    "app/services/youtube_thumbnail_learner.py",
]

for file_path in files_to_fix:
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        continue

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already has import logging
    if re.search(r'^import logging$', content, re.MULTILINE):
        print(f"✓ {file_path} already has logging import")
        continue

    # Check if uses logging.getLogger
    if 'logging.getLogger' not in content:
        print(f"- {file_path} doesn't use logging.getLogger")
        continue

    # Add import logging after docstring or at the beginning
    lines = content.split('\n')
    insert_index = 0

    # Find where to insert
    in_docstring = False
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            if not in_docstring:
                in_docstring = True
            elif in_docstring and (line.strip().endswith('"""') or line.strip().endswith("'''")):
                insert_index = i + 1
                break
        elif not in_docstring and (line.startswith('import ') or line.startswith('from ')):
            insert_index = i
            break

    # Insert import logging
    lines.insert(insert_index, 'import logging')

    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✓ Added logging import to {file_path}")

print("\nDone!")
