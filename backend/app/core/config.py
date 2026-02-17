"""애플리케이션 설정 관리"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # Paths
    BASE_DIR: str = "/Volumes/Extreme SSD/02_GitHub.nosync/0030_OmniVibePro/backend"
    OUTPUTS_DIR: str = "./outputs"

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

    # Anthropic Claude
    ANTHROPIC_API_KEY: str

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
    HEYGEN_API_ENDPOINT: str = "https://api.heygen.com/v1"

    # Nano Banana (옵션)
    BANANA_API_KEY: str | None = None
    CHARACTER_STORAGE_PATH: str = "./outputs/characters"

    # Lipsync Settings
    WAV2LIP_MODEL_PATH: str | None = None
    LIPSYNC_GPU_ENABLED: bool = False
    LIPSYNC_OUTPUT_DIR: str = "./outputs/lipsync"

    # 소셜 미디어
    YOUTUBE_OAUTH_CLIENT_ID: str | None = None
    YOUTUBE_OAUTH_CLIENT_SECRET: str | None = None
    INSTAGRAM_ACCESS_TOKEN: str | None = None
    FACEBOOK_ACCESS_TOKEN: str | None = None

    # Unsplash (이미지 검색)
    UNSPLASH_ACCESS_KEY: str | None = None

    # JWT Authentication (Week 5)
    SECRET_KEY: str  # JWT 서명용 비밀 키 (이미 위에 정의됨)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth 2.0 (Week 5)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3020/api/auth/google/callback"  # FRONTEND_URL 설정 시 자동으로 맞게 변경할 것

    # Stripe (Week 5)
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # Frontend URL (프로덕션 배포 시 환경변수로 주입)
    FRONTEND_URL: str = "http://localhost:3020"

    # CORS (콤마 구분 다중 도메인 지원)
    CORS_ORIGINS: str = "http://localhost:3020,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # .env에 있지만 모델에 없는 필드 무시


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스"""
    return Settings()


# Global settings instance
settings = get_settings()
