"""보안 기능 테스트"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import hashlib

from app.main import app
from app.auth.jwt_handler import create_access_token, create_refresh_token, verify_token
from app.auth.password import get_password_hash, verify_password
from app.validators.security_validators import (
    sanitize_text,
    validate_file_type,
    prevent_path_traversal,
    sanitize_filename,
)

client = TestClient(app)


# ==================== Authentication Tests ====================

def test_register_success():
    """사용자 등록 성공 테스트"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert "user_id" in data


def test_register_weak_password():
    """약한 비밀번호로 등록 시도 (실패)"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "weak",  # 너무 짧음
        },
    )

    assert response.status_code == 422  # Validation error


def test_login_success():
    """로그인 성공 테스트"""
    # 먼저 사용자 등록
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login_test@example.com",
            "name": "Login Test",
            "password": "SecurePass123!",
        },
    )

    # 로그인 시도
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """잘못된 자격 증명으로 로그인 시도 (실패)"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPass123!",
        },
    )

    assert response.status_code == 401


def test_access_protected_endpoint_without_token():
    """인증 없이 보호된 엔드포인트 접근 (실패)"""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 403  # Forbidden


def test_access_protected_endpoint_with_token():
    """토큰으로 보호된 엔드포인트 접근 (성공)"""
    # 사용자 등록 및 로그인
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "protected_test@example.com",
            "name": "Protected Test",
            "password": "SecurePass123!",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "protected_test@example.com",
            "password": "SecurePass123!",
        },
    )

    access_token = login_response.json()["access_token"]

    # 보호된 엔드포인트 접근
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "protected_test@example.com"


def test_refresh_token():
    """리프레시 토큰으로 액세스 토큰 갱신"""
    # 로그인
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh_test@example.com",
            "password": "SecurePass123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    # 토큰 갱신
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


# ==================== JWT Tests ====================

def test_create_and_verify_access_token():
    """액세스 토큰 생성 및 검증"""
    token_data = {
        "sub": "user_123",
        "email": "test@example.com",
        "role": "user",
    }

    token = create_access_token(token_data)
    assert token is not None

    payload = verify_token(token, token_type="access")
    assert payload is not None
    assert payload["sub"] == "user_123"
    assert payload["email"] == "test@example.com"


def test_verify_expired_token():
    """만료된 토큰 검증 (실패)"""
    token_data = {"sub": "user_123"}
    expires_delta = timedelta(seconds=-1)  # 이미 만료됨

    token = create_access_token(token_data, expires_delta)
    payload = verify_token(token, token_type="access")

    assert payload is None


def test_verify_wrong_token_type():
    """잘못된 토큰 타입 검증 (실패)"""
    token_data = {"sub": "user_123"}
    access_token = create_access_token(token_data)

    # Access token을 Refresh token으로 검증 시도
    payload = verify_token(access_token, token_type="refresh")
    assert payload is None


# ==================== Password Tests ====================

def test_password_hashing():
    """비밀번호 해싱 및 검증"""
    password = "SecurePassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# ==================== Input Validation Tests ====================

def test_sanitize_text_xss():
    """XSS 공격 방지 테스트"""
    malicious_input = "<script>alert('XSS')</script>"
    sanitized = sanitize_text(malicious_input)

    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized


def test_sanitize_text_with_javascript():
    """JavaScript 삽입 방지 테스트"""
    malicious_input = '<img src=x onerror="alert(1)">'
    sanitized = sanitize_text(malicious_input)

    assert "onerror" not in sanitized


def test_prevent_path_traversal():
    """Path Traversal 공격 방지 테스트"""
    dangerous_paths = [
        "../../etc/passwd",
        "../../../etc/shadow",
        "../../../../root/.ssh/id_rsa",
        "file.txt/../../../etc/passwd",
    ]

    for path in dangerous_paths:
        safe_path = prevent_path_traversal(path)
        assert safe_path is None


def test_prevent_path_traversal_safe():
    """안전한 파일명 테스트"""
    safe_paths = [
        "document.pdf",
        "image.jpg",
        "script.py",
    ]

    for path in safe_paths:
        safe_path = prevent_path_traversal(path)
        assert safe_path is not None


def test_sanitize_filename():
    """파일명 정제 테스트"""
    assert sanitize_filename("my file (1).jpg") == "my_file_1.jpg"
    assert sanitize_filename("file@#$%.txt") == "file.txt"
    assert sanitize_filename("../../etc/passwd") == ".._etc_passwd"


# ==================== Rate Limiting Tests ====================

def test_rate_limit_basic():
    """기본 Rate Limit 테스트"""
    # 여러 번 요청 시도
    responses = []
    for _ in range(15):
        response = client.post(
            "/api/v1/audio/generate",
            json={"script": "Test", "voice_id": "voice_123"},
        )
        responses.append(response)

    # 일부 요청은 성공, 일부는 429 (Too Many Requests) 예상
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes  # Rate limit exceeded


def test_rate_limit_headers():
    """Rate Limit 헤더 확인"""
    response = client.get("/api/v1/health")

    # Rate Limit 헤더 확인
    if "X-RateLimit-Limit" in response.headers:
        assert int(response.headers["X-RateLimit-Limit"]) > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0


# ==================== Security Headers Tests ====================

def test_security_headers_present():
    """보안 헤더 존재 확인"""
    response = client.get("/")

    assert "Content-Security-Policy" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-Content-Type-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Referrer-Policy" in response.headers


def test_x_frame_options():
    """X-Frame-Options 헤더 값 확인"""
    response = client.get("/")
    assert response.headers["X-Frame-Options"] == "DENY"


def test_content_security_policy():
    """CSP 헤더 값 확인"""
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp


# ==================== API Key Tests ====================

def test_create_api_key():
    """API 키 생성 테스트"""
    # 먼저 로그인하여 토큰 획득
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "apikey_test@example.com",
            "password": "SecurePass123!",
        },
    )

    access_token = login_response.json()["access_token"]

    # API 키 생성
    response = client.post(
        "/api/v1/auth/api-keys",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "Test API Key",
            "expires_in_days": 30,
            "rate_limit": 1000,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("ovp_")


def test_list_api_keys():
    """API 키 목록 조회 테스트"""
    # 로그인
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "apikey_test@example.com",
            "password": "SecurePass123!",
        },
    )

    access_token = login_response.json()["access_token"]

    # API 키 목록 조회
    response = client.get(
        "/api/v1/auth/api-keys",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ==================== RBAC Tests ====================

def test_admin_only_endpoint_as_user():
    """관리자 전용 엔드포인트에 일반 사용자 접근 (실패)"""
    # 일반 사용자로 로그인
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "regular_user@example.com",
            "password": "SecurePass123!",
        },
    )

    access_token = login_response.json()["access_token"]

    # 관리자 전용 엔드포인트 접근 시도
    response = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403  # Forbidden


# ==================== Audit Log Tests ====================

@pytest.mark.asyncio
async def test_audit_log_creation():
    """감사 로그 생성 테스트"""
    from app.services.audit_logger import log_auth_event

    await log_auth_event(
        event_type="login_success",
        user_id="user_test123",
        email="test@example.com",
        status="success",
    )

    # 로그가 생성되었는지 확인
    # (실제 구현에서는 Neo4j 쿼리로 확인)


@pytest.mark.asyncio
async def test_get_user_audit_logs():
    """사용자 감사 로그 조회 테스트"""
    from app.services.audit_logger import get_user_audit_logs

    logs = await get_user_audit_logs(
        user_id="user_test123",
        limit=10,
    )

    assert isinstance(logs, list)


# ==================== Integration Tests ====================

def test_complete_auth_flow():
    """전체 인증 흐름 테스트"""
    # 1. 회원가입
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow_test@example.com",
            "name": "Flow Test",
            "password": "SecurePass123!",
        },
    )
    assert register_response.status_code == 201

    # 2. 로그인
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "flow_test@example.com",
            "password": "SecurePass123!",
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # 3. 인증된 요청
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200

    # 4. 비밀번호 변경
    password_change_response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!",
        },
    )
    assert password_change_response.status_code == 204

    # 5. 새 비밀번호로 로그인
    new_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "flow_test@example.com",
            "password": "NewSecurePass456!",
        },
    )
    assert new_login_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
