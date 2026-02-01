#!/usr/bin/env python3
"""Fix logfire.get_logger to logging.getLogger"""
import os
import re
from pathlib import Path

def fix_file(filepath):
    """Fix a single file"""
    with open(filepath, 'r') as f:
        content = f.read()

    # Check if file uses logging.getLogger
    if 'logging.getLogger' not in content:
        return False

    # Check if import logging exists
    if not re.search(r'^import logging$', content, re.MULTILINE):
        # Add import logging at the top
        lines = content.split('\n')

        # Find the first import or from statement
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('"""') or line.startswith("'''"):
                # Skip docstring
                continue
            if line.startswith('import ') or line.startswith('from '):
                insert_index = i
                break

        lines.insert(insert_index, 'import logging')
        content = '\n'.join(lines)

    # Remove logfire import if only used for get_logger
    if 'logfire.get_logger' not in content and re.search(r'^import logfire$', content, re.MULTILINE):
        content = re.sub(r'^import logfire\n?', '', content, flags=re.MULTILINE)

    with open(filepath, 'w') as f:
        f.write(content)

    return True

def main():
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / 'app'

    count = 0
    for py_file in app_dir.rglob('*.py'):
        if fix_file(py_file):
            print(f"Fixed: {py_file}")
            count += 1

    print(f"\nTotal files fixed: {count}")

if __name__ == '__main__':
    main()
