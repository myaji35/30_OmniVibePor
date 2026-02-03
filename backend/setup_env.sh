#!/bin/bash
set -e
echo "Starting Backend Surgery for OmniVibe Pro..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Backend Surgery Successful."
