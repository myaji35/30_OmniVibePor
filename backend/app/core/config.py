"""애플리케이션 설정 관리"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str

    # Redis & Celery
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Logfire
    LOGFIRE_TOKEN: str

    # OpenAI
    OPENAI_API_KEY: str

    # ElevenLabs
    ELEVENLABS_API_KEY: str

    # Google
    GOOGLE_VEO_API_KEY: str
    GOOGLE_SHEETS_CREDENTIALS_PATH: str
    YOUTUBE_API_KEY: str

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "omnivibe-thumbnails"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # HeyGen (옵션)
    HEYGEN_API_KEY: str | None = None

    # Nano Banana (옵션)
    BANANA_API_KEY: str | None = None

    # 소셜 미디어
    YOUTUBE_OAUTH_CLIENT_ID: str | None = None
    YOUTUBE_OAUTH_CLIENT_SECRET: str | None = None
    INSTAGRAM_ACCESS_TOKEN: str | None = None
    FACEBOOK_ACCESS_TOKEN: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스"""
    return Settings()
