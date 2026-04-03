FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl sox libsox-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] \
    torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install CosyVoice from PyPI
RUN pip install --no-cache-dir cosyvoice

# Download model on first run (or mount volume)
COPY server.py /app/server.py
COPY download_model.py /app/download_model.py

EXPOSE 9880

CMD ["python", "server.py", "--port", "9880"]
