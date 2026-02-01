FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (ffmpeg, opencv 등)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry==1.7.1

# 의존성 파일 복사
COPY pyproject.toml poetry.lock* ./

# 의존성 설치 (가상환경 생성 안함)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# 애플리케이션 코드 복사
COPY . .

# 출력 디렉토리 생성
RUN mkdir -p /app/outputs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
