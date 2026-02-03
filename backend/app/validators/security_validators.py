"""보안 검증 및 입력 검증"""
import os
import re
import html
from typing import Optional, List
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
import mimetypes


# ==================== XSS Prevention ====================

def sanitize_text(text: str) -> str:
    """
    XSS 공격 방지를 위한 텍스트 정제

    HTML 특수 문자를 이스케이프 처리합니다.

    Args:
        text: 입력 텍스트

    Returns:
        정제된 텍스트

    Example:
        >>> sanitize_text("<script>alert('XSS')</script>")
        "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
    """
    if not text:
        return text

    # HTML 이스케이프
    sanitized = html.escape(text)

    # 추가 위험 패턴 제거
    dangerous_patterns = [
        r'javascript:',
        r'on\w+\s*=',  # onclick, onerror 등
        r'<iframe',
        r'<object',
        r'<embed',
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized


def remove_sql_injection_patterns(text: str) -> str:
    """
    SQL Injection 패턴 제거

    Args:
        text: 입력 텍스트

    Returns:
        정제된 텍스트
    """
    if not text:
        return text

    # SQL Injection 위험 패턴
    sql_patterns = [
        r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
        r";\s*DROP\s+TABLE",
        r";\s*DELETE\s+FROM",
        r"UNION\s+SELECT",
        r"--",
        r"/\*.*?\*/",
    ]

    sanitized = text
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized


def remove_cypher_injection_patterns(text: str) -> str:
    """
    Cypher Injection 패턴 제거 (Neo4j)

    Args:
        text: 입력 텍스트

    Returns:
        정제된 텍스트
    """
    if not text:
        return text

    # Cypher Injection 위험 패턴
    cypher_patterns = [
        r"MATCH.*DETACH\s+DELETE",
        r";\s*DROP",
        r"CALL\s+dbms\.",
    ]

    sanitized = text
    for pattern in cypher_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized


# ==================== File Upload Validation ====================

# 허용된 파일 타입
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
    "application/vnd.ms-powerpoint",  # PPT
}

# 최대 파일 크기 (바이트)
MAX_FILE_SIZE = {
    "image": 10 * 1024 * 1024,  # 10MB
    "audio": 50 * 1024 * 1024,  # 50MB
    "video": 500 * 1024 * 1024,  # 500MB
    "document": 20 * 1024 * 1024,  # 20MB
}


def validate_file_type(file: UploadFile, allowed_types: set) -> bool:
    """
    파일 타입 검증

    Args:
        file: 업로드된 파일
        allowed_types: 허용된 MIME 타입 집합

    Returns:
        유효 여부
    """
    # MIME 타입 확인
    if file.content_type not in allowed_types:
        return False

    # 파일 확장자 확인
    filename = file.filename
    if not filename:
        return False

    ext = os.path.splitext(filename)[1].lower()
    guessed_type, _ = mimetypes.guess_type(filename)

    # 확장자와 MIME 타입 일치 확인
    if guessed_type and guessed_type not in allowed_types:
        return False

    return True


def validate_file_size(file: UploadFile, max_size: int) -> bool:
    """
    파일 크기 검증

    Args:
        file: 업로드된 파일
        max_size: 최대 크기 (바이트)

    Returns:
        유효 여부
    """
    # 파일 크기 확인
    file.file.seek(0, 2)  # 파일 끝으로 이동
    file_size = file.file.tell()
    file.file.seek(0)  # 파일 시작으로 되돌리기

    return file_size <= max_size


async def validate_file_upload(
    file: UploadFile,
    file_category: str = "image"
) -> None:
    """
    파일 업로드 검증

    Args:
        file: 업로드된 파일
        file_category: 파일 카테고리 ("image", "audio", "video", "document")

    Raises:
        HTTPException: 파일이 유효하지 않을 경우
    """
    # 파일 카테고리별 허용 타입
    allowed_types_map = {
        "image": ALLOWED_IMAGE_TYPES,
        "audio": ALLOWED_AUDIO_TYPES,
        "video": ALLOWED_VIDEO_TYPES,
        "document": ALLOWED_DOCUMENT_TYPES,
    }

    allowed_types = allowed_types_map.get(file_category)
    if not allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file category: {file_category}"
        )

    # 파일 타입 검증
    if not validate_file_type(file, allowed_types):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )

    # 파일 크기 검증
    max_size = MAX_FILE_SIZE.get(file_category, 10 * 1024 * 1024)
    if not validate_file_size(file, max_size):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size / (1024 * 1024):.2f}MB"
        )

    # 파일명 검증
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    # Path Traversal 방지
    safe_filename = prevent_path_traversal(file.filename)
    if not safe_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )


# ==================== Path Traversal Prevention ====================

def prevent_path_traversal(filename: str) -> Optional[str]:
    """
    Path Traversal 공격 방지

    Args:
        filename: 파일명

    Returns:
        안전한 파일명 또는 None (위험한 경우)

    Example:
        >>> prevent_path_traversal("../../etc/passwd")
        None
        >>> prevent_path_traversal("image.jpg")
        "image.jpg"
    """
    if not filename:
        return None

    # 위험한 패턴 확인
    dangerous_patterns = [
        '..',
        '/',
        '\\',
        '\0',
    ]

    for pattern in dangerous_patterns:
        if pattern in filename:
            return None

    # 상대 경로 제거
    filename = os.path.basename(filename)

    # 빈 문자열 확인
    if not filename or filename == '.':
        return None

    return filename


def sanitize_filename(filename: str) -> str:
    """
    파일명 정제

    안전한 문자만 허용하고 나머지는 제거합니다.

    Args:
        filename: 원본 파일명

    Returns:
        정제된 파일명

    Example:
        >>> sanitize_filename("my file (1).jpg")
        "my_file_1.jpg"
    """
    if not filename:
        return "untitled"

    # 확장자 분리
    name, ext = os.path.splitext(filename)

    # 안전한 문자만 유지 (알파벳, 숫자, 언더스코어, 하이픈)
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    # 연속된 언더스코어 제거
    safe_name = re.sub(r'_+', '_', safe_name)

    # 앞뒤 언더스코어 제거
    safe_name = safe_name.strip('_')

    # 빈 이름 처리
    if not safe_name:
        safe_name = "file"

    # 확장자 추가 (안전한 문자만)
    safe_ext = re.sub(r'[^a-zA-Z0-9.]', '', ext)

    return f"{safe_name}{safe_ext}"


# ==================== URL Validation ====================

def validate_url(url: str) -> bool:
    """
    URL 검증

    Args:
        url: URL 문자열

    Returns:
        유효 여부
    """
    if not url:
        return False

    # URL 패턴
    url_pattern = re.compile(
        r'^https?://'  # http:// 또는 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 도메인
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # 포트
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    return bool(url_pattern.match(url))


def validate_email(email: str) -> bool:
    """
    이메일 검증

    Args:
        email: 이메일 주소

    Returns:
        유효 여부
    """
    if not email:
        return False

    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    return bool(email_pattern.match(email))


# ==================== Input Sanitization ====================

def sanitize_user_input(
    data: dict,
    text_fields: Optional[List[str]] = None
) -> dict:
    """
    사용자 입력 데이터 전체 정제

    Args:
        data: 입력 데이터 딕셔너리
        text_fields: 정제할 텍스트 필드 목록

    Returns:
        정제된 데이터
    """
    if not data:
        return data

    if text_fields is None:
        text_fields = []

    sanitized = data.copy()

    for field in text_fields:
        if field in sanitized and isinstance(sanitized[field], str):
            sanitized[field] = sanitize_text(sanitized[field])

    return sanitized
