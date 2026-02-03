"""환경 변수 및 시크릿 관리"""
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """환경 변수 및 시크릿 관리 클래스"""

    # 필수 환경 변수
    REQUIRED_SECRETS = [
        "SECRET_KEY",
        "REDIS_URL",
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "OPENAI_API_KEY",
    ]

    # 선택적 환경 변수 (경고만 표시)
    OPTIONAL_SECRETS = [
        "ELEVENLABS_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_VEO_API_KEY",
        "PINECONE_API_KEY",
        "CLOUDINARY_API_KEY",
        "HEYGEN_API_KEY",
        "LOGFIRE_TOKEN",
    ]

    # 민감 정보 패턴 (로그에서 마스킹)
    SENSITIVE_PATTERNS = [
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "key",
        "credential",
    ]

    @staticmethod
    def validate_required_secrets() -> bool:
        """
        필수 환경 변수 검증

        Returns:
            모든 필수 환경 변수가 설정되어 있으면 True

        Raises:
            SystemExit: 필수 환경 변수가 누락된 경우
        """
        missing = []

        for secret in SecretsManager.REQUIRED_SECRETS:
            value = os.getenv(secret)
            if not value or value == "your_" + secret.lower():
                missing.append(secret)

        if missing:
            logger.error(
                f"Missing required environment variables: {', '.join(missing)}"
            )
            logger.error(
                "Please set these variables in your .env file or environment"
            )
            sys.exit(1)

        logger.info("All required secrets validated successfully")
        return True

    @staticmethod
    def check_optional_secrets() -> Dict[str, bool]:
        """
        선택적 환경 변수 확인

        Returns:
            환경 변수별 설정 여부 딕셔너리
        """
        status = {}

        for secret in SecretsManager.OPTIONAL_SECRETS:
            value = os.getenv(secret)
            is_set = bool(value and value != "your_" + secret.lower())
            status[secret] = is_set

            if not is_set:
                logger.warning(
                    f"Optional secret '{secret}' is not set. "
                    f"Some features may be unavailable."
                )

        return status

    @staticmethod
    def mask_sensitive_value(key: str, value: str) -> str:
        """
        민감 정보 마스킹

        Args:
            key: 환경 변수 키
            value: 값

        Returns:
            마스킹된 값

        Example:
            >>> SecretsManager.mask_sensitive_value("API_KEY", "sk-1234567890abcdef")
            "sk-12***************ef"
        """
        if not value:
            return ""

        # 민감 정보 키 확인
        is_sensitive = any(
            pattern in key.lower()
            for pattern in SecretsManager.SENSITIVE_PATTERNS
        )

        if not is_sensitive:
            return value

        # 짧은 값은 전체 마스킹
        if len(value) <= 8:
            return "*" * len(value)

        # 앞 4자, 뒤 2자만 표시
        return f"{value[:4]}{'*' * (len(value) - 6)}{value[-2:]}"

    @staticmethod
    def get_safe_config() -> Dict[str, str]:
        """
        민감 정보가 마스킹된 설정 정보 조회

        Returns:
            마스킹된 설정 딕셔너리
        """
        from app.core.config import get_settings

        settings = get_settings()
        safe_config = {}

        for key, value in settings.model_dump().items():
            if isinstance(value, str):
                safe_config[key] = SecretsManager.mask_sensitive_value(key, value)
            else:
                safe_config[key] = value

        return safe_config

    @staticmethod
    def validate_secret_format(secret_name: str, value: str) -> bool:
        """
        시크릿 형식 검증

        Args:
            secret_name: 시크릿 이름
            value: 값

        Returns:
            유효 여부
        """
        if not value:
            return False

        # URL 형식 검증
        if "URL" in secret_name or "URI" in secret_name:
            url_pattern = re.compile(
                r'^(https?|redis|mongodb|neo4j)://.*'
            )
            return bool(url_pattern.match(value))

        # API 키 형식 검증 (일반적 패턴)
        if "API_KEY" in secret_name:
            # 최소 길이 확인
            if len(value) < 16:
                return False

            # 영숫자, 하이픈, 언더스코어만 허용
            if not re.match(r'^[a-zA-Z0-9_-]+$', value):
                return False

        # SECRET_KEY 검증
        if secret_name == "SECRET_KEY":
            # 최소 32자
            if len(value) < 32:
                logger.warning(
                    "SECRET_KEY should be at least 32 characters long"
                )
                return False

        return True

    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """
        랜덤 SECRET_KEY 생성

        Args:
            length: 키 길이

        Returns:
            랜덤 키
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def load_env_file(env_file: Path = Path(".env")) -> bool:
        """
        .env 파일 로드

        Args:
            env_file: .env 파일 경로

        Returns:
            로드 성공 여부
        """
        if not env_file.exists():
            logger.warning(f".env file not found at {env_file}")
            return False

        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()

                    # 주석이나 빈 줄 무시
                    if not line or line.startswith("#"):
                        continue

                    # KEY=VALUE 형식 파싱
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        # 이미 설정된 환경 변수는 덮어쓰지 않음
                        if key not in os.environ:
                            os.environ[key] = value

            logger.info(f"Loaded environment variables from {env_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load .env file: {e}")
            return False

    @staticmethod
    def check_file_permissions(env_file: Path = Path(".env")) -> bool:
        """
        .env 파일 권한 검증 (Unix 시스템)

        Args:
            env_file: .env 파일 경로

        Returns:
            권한이 안전하면 True
        """
        if not env_file.exists():
            return True

        # Windows는 스킵
        if sys.platform == "win32":
            return True

        try:
            import stat

            file_stat = os.stat(env_file)
            mode = file_stat.st_mode

            # 다른 사용자가 읽을 수 있는지 확인
            if mode & stat.S_IROTH or mode & stat.S_IWOTH:
                logger.warning(
                    f".env file has insecure permissions. "
                    f"Run: chmod 600 {env_file}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check file permissions: {e}")
            return True  # 확인 실패 시 계속 진행


def initialize_secrets() -> None:
    """
    애플리케이션 시작 시 시크릿 초기화 및 검증

    Raises:
        SystemExit: 필수 환경 변수가 누락된 경우
    """
    # .env 파일 로드
    env_file = Path(__file__).parent.parent.parent / ".env"
    SecretsManager.load_env_file(env_file)

    # 파일 권한 확인
    SecretsManager.check_file_permissions(env_file)

    # 필수 환경 변수 검증
    SecretsManager.validate_required_secrets()

    # 선택적 환경 변수 확인
    optional_status = SecretsManager.check_optional_secrets()

    # 활성화된 기능 로그
    enabled_features = [
        key.replace("_API_KEY", "").replace("_TOKEN", "")
        for key, is_set in optional_status.items()
        if is_set
    ]

    if enabled_features:
        logger.info(f"Enabled features: {', '.join(enabled_features)}")
