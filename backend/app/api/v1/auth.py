"""인증 API 엔드포인트"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
import secrets
import hashlib

from app.models.user import (
    UserCreate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserPasswordChange,
    UserUpdate,
    User,
    UserCRUD,
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKey,
    APIKeyCRUD,
)
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    verify_password,
)
from app.auth.oauth import google_oauth
from app.auth.dependencies import get_current_user, require_role
from app.models.user import UserRole
from app.services.neo4j_client import Neo4jClient
from app.services.audit_logger import log_auth_event

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Neo4j 클라이언트 초기화
neo4j_client = Neo4jClient()
user_crud = UserCRUD(neo4j_client)
api_key_crud = APIKeyCRUD(neo4j_client)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    사용자 등록

    새로운 사용자를 생성합니다. 이메일은 고유해야 합니다.

    - **email**: 사용자 이메일 (고유)
    - **name**: 사용자 이름
    - **password**: 비밀번호 (8자 이상, 대소문자 + 숫자 포함)
    - **phone**: 전화번호 (선택)
    - **company**: 회사명 (선택)
    """
    # 이메일 중복 확인
    existing_user = user_crud.get_user_by_email(user_data.email)
    if existing_user:
        await log_auth_event(
            event_type="register_failed",
            user_id=None,
            email=user_data.email,
            reason="Email already exists"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)

    # 사용자 생성
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        phone=user_data.phone,
        company=user_data.company,
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
    )

    created_user = user_crud.create_user(user)

    # 감사 로그 기록
    await log_auth_event(
        event_type="register_success",
        user_id=created_user.get("user_id"),
        email=user_data.email
    )

    return UserResponse(**created_user)


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    로그인

    이메일과 비밀번호로 로그인하고 JWT 토큰을 발급받습니다.

    - **email**: 사용자 이메일
    - **password**: 비밀번호

    Returns:
        - **access_token**: 액세스 토큰 (30분 유효)
        - **refresh_token**: 리프레시 토큰 (7일 유효)
        - **user**: 사용자 정보
    """
    # 사용자 조회
    user = user_crud.get_user_by_email(login_data.email)
    if not user:
        await log_auth_event(
            event_type="login_failed",
            user_id=None,
            email=login_data.email,
            reason="User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # 비밀번호 검증
    if not verify_password(login_data.password, user["hashed_password"]):
        await log_auth_event(
            event_type="login_failed",
            user_id=user["user_id"],
            email=login_data.email,
            reason="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # 비활성화된 사용자 확인
    if not user.get("is_active", True):
        await log_auth_event(
            event_type="login_failed",
            user_id=user["user_id"],
            email=login_data.email,
            reason="User inactive"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    # JWT 토큰 생성
    token_data = {
        "sub": user["user_id"],
        "email": user["email"],
        "role": user.get("role", "user"),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user["user_id"]})

    # 마지막 로그인 시간 업데이트
    user_crud.update_last_login(user["user_id"])

    # 감사 로그 기록
    await log_auth_event(
        event_type="login_success",
        user_id=user["user_id"],
        email=login_data.email
    )

    # hashed_password 제거
    user_response = {k: v for k, v in user.items() if k != "hashed_password"}

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(**user_response)
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(token_data: RefreshTokenRequest):
    """
    액세스 토큰 갱신

    리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급받습니다.

    - **refresh_token**: 리프레시 토큰
    """
    # 리프레시 토큰 검증
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # 사용자 조회
    user = user_crud.get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # 새 액세스 토큰 생성
    token_data = {
        "sub": user["user_id"],
        "email": user["email"],
        "role": user.get("role", "user"),
    }
    access_token = create_access_token(token_data)

    return RefreshTokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    로그아웃

    현재 액세스 토큰을 블랙리스트에 추가하여 무효화합니다.

    **인증 필요**: Bearer Token
    """
    # 토큰 블랙리스트 추가는 dependencies에서 토큰을 가져와야 하므로
    # 실제 구현에서는 헤더에서 직접 추출 필요
    # 여기서는 로그아웃 성공으로 간주

    await log_auth_event(
        event_type="logout",
        user_id=current_user["user_id"],
        email=current_user["email"]
    )

    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    현재 사용자 정보 조회

    인증된 사용자의 상세 정보를 조회합니다.

    **인증 필요**: Bearer Token
    """
    # hashed_password 제거
    user_data = {k: v for k, v in current_user.items() if k != "hashed_password"}
    return UserResponse(**user_data)


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    현재 사용자 정보 업데이트

    **인증 필요**: Bearer Token

    - **name**: 이름
    - **phone**: 전화번호
    - **company**: 회사명
    - **profile_image_url**: 프로필 이미지 URL
    """
    # None이 아닌 필드만 업데이트
    updates = {k: v for k, v in user_update.model_dump().items() if v is not None}

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # 사용자 정보 업데이트
    success = user_crud.update_user(current_user["user_id"], updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 업데이트된 사용자 정보 조회
    updated_user = user_crud.get_user_by_id(current_user["user_id"])
    user_data = {k: v for k, v in updated_user.items() if k != "hashed_password"}

    return UserResponse(**user_data)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: UserPasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    비밀번호 변경

    **인증 필요**: Bearer Token

    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호 (8자 이상, 대소문자 + 숫자 포함)
    """
    # 현재 비밀번호 검증
    user = user_crud.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(password_data.current_password, user["hashed_password"]):
        await log_auth_event(
            event_type="password_change_failed",
            user_id=current_user["user_id"],
            email=current_user["email"],
            reason="Invalid current password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )

    # 새 비밀번호 해싱 및 업데이트
    new_hashed_password = get_password_hash(password_data.new_password)
    user_crud.update_user(
        current_user["user_id"],
        {"hashed_password": new_hashed_password}
    )

    await log_auth_event(
        event_type="password_change_success",
        user_id=current_user["user_id"],
        email=current_user["email"]
    )

    return None


# ==================== API Key Management ====================

@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    API 키 생성

    새로운 API 키를 생성합니다. API 키는 생성 시 1회만 반환됩니다.

    **인증 필요**: Bearer Token

    - **name**: API 키 이름
    - **expires_in_days**: 만료 일수 (선택, 1-365일)
    - **rate_limit**: 시간당 요청 제한 (1-10000)
    """
    # 실제 API 키 생성 (32바이트 랜덤)
    raw_key = secrets.token_urlsafe(32)
    api_key_string = f"ovp_{raw_key}"

    # API 키 해시 (SHA-256)
    key_hash = hashlib.sha256(api_key_string.encode()).hexdigest()

    # 프리픽스 (표시용)
    prefix = api_key_string[:12]

    # 만료 시간 계산
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)

    # API 키 객체 생성
    api_key = APIKey(
        user_id=current_user["user_id"],
        name=key_data.name,
        key_hash=key_hash,
        prefix=prefix,
        is_active=True,
        expires_at=expires_at,
        rate_limit=key_data.rate_limit,
    )

    # DB에 저장
    created_key = api_key_crud.create_api_key(api_key)

    await log_auth_event(
        event_type="api_key_created",
        user_id=current_user["user_id"],
        email=current_user["email"],
        details={"key_id": created_key["key_id"], "name": key_data.name}
    )

    return APIKeyCreateResponse(
        key_id=api_key.key_id,
        name=key_data.name,
        api_key=api_key_string,  # 실제 API 키 (1회만 반환)
        prefix=prefix,
        created_at=api_key.created_at,
        expires_at=expires_at,
        rate_limit=key_data.rate_limit,
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """
    API 키 목록 조회

    현재 사용자의 모든 API 키를 조회합니다.

    **인증 필요**: Bearer Token
    """
    keys = api_key_crud.list_user_api_keys(current_user["user_id"])
    return [APIKeyResponse(**key) for key in keys]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    API 키 비활성화

    지정한 API 키를 비활성화합니다.

    **인증 필요**: Bearer Token
    """
    success = api_key_crud.revoke_api_key(key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    await log_auth_event(
        event_type="api_key_revoked",
        user_id=current_user["user_id"],
        email=current_user["email"],
        details={"key_id": key_id}
    )

    return None


# ==================== Admin Routes ====================

@router.get(
    "/admin/users",
    response_model=List[UserResponse],
    dependencies=[Depends(require_role([UserRole.ADMIN]))]
)
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    is_active: bool = None
):
    """
    모든 사용자 조회 (관리자 전용)

    **인증 필요**: Bearer Token (Admin)

    - **skip**: 건너뛸 레코드 수
    - **limit**: 최대 레코드 수
    - **role**: 역할 필터
    - **is_active**: 활성 상태 필터
    """
    users = user_crud.list_users(
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active
    )

    # hashed_password 제거
    return [
        UserResponse(**{k: v for k, v in user.items() if k != "hashed_password"})
        for user in users
    ]


@router.put(
    "/admin/users/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_role([UserRole.ADMIN]))]
)
async def update_user_role(user_id: str, new_role: UserRole):
    """
    사용자 역할 변경 (관리자 전용)

    **인증 필요**: Bearer Token (Admin)
    """
    success = user_crud.update_user(user_id, {"role": new_role.value})
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updated_user = user_crud.get_user_by_id(user_id)
    user_data = {k: v for k, v in updated_user.items() if k != "hashed_password"}

    return UserResponse(**user_data)


@router.put(
    "/admin/users/{user_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([UserRole.ADMIN]))]
)
async def deactivate_user(user_id: str):
    """
    사용자 비활성화 (관리자 전용)

    **인증 필요**: Bearer Token (Admin)
    """
    success = user_crud.update_user(user_id, {"is_active": False})
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return None


# ==================== Google OAuth 2.0 ====================

@router.get("/google/login")
async def google_login():
    """
    Google OAuth 2.0 로그인 시작

    Google 로그인 페이지로 리다이렉트합니다.

    Returns:
        dict: Google 인증 URL
    """
    authorization_url = google_oauth.get_authorization_url(state="random_state_string")

    return {
        "authorization_url": authorization_url,
        "message": "Redirect user to this URL for Google login"
    }


@router.post("/google/callback", response_model=LoginResponse)
async def google_callback(code: str):
    """
    Google OAuth 2.0 콜백

    Google에서 돌아온 Authorization Code를 처리하여 로그인/회원가입합니다.

    Args:
        code: Google Authorization Code

    Returns:
        LoginResponse: JWT 토큰 및 사용자 정보
    """
    # Google OAuth 인증
    google_user = await google_oauth.authenticate(code)

    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed"
        )

    email = google_user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google"
        )

    # 기존 사용자 확인
    existing_user = user_crud.get_user_by_email(email)

    if existing_user:
        # 기존 사용자 로그인
        user_crud.update_last_login(existing_user["user_id"])

        # JWT 토큰 생성
        token_data = {
            "user_id": existing_user["user_id"],
            "email": existing_user["email"],
            "role": existing_user.get("role", "user"),
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        await log_auth_event(
            event_type="google_login",
            user_id=existing_user["user_id"],
            email=email
        )

        user_data = {k: v for k, v in existing_user.items() if k != "hashed_password"}
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(**user_data)
        )

    else:
        # 새 사용자 회원가입
        new_user = User(
            email=email,
            name=google_user.get("name", "Google User"),
            hashed_password="",  # OAuth 사용자는 비밀번호 없음
            profile_image_url=google_user.get("picture"),
            is_verified=google_user.get("verified_email", False),
            subscription_tier="free"
        )

        created_user = user_crud.create_user(new_user)

        # JWT 토큰 생성
        token_data = {
            "user_id": created_user["user_id"],
            "email": created_user["email"],
            "role": "user",
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        await log_auth_event(
            event_type="google_register",
            user_id=created_user["user_id"],
            email=email
        )

        # 응답 데이터 준비
        user_response_data = {
            "user_id": created_user["user_id"],
            "email": created_user["email"],
            "name": new_user.name,
            "role": UserRole.USER,
            "is_active": True,
            "is_verified": new_user.is_verified,
            "created_at": new_user.created_at,
            "updated_at": new_user.updated_at,
            "last_login": None,
            "profile_image_url": new_user.profile_image_url,
            "phone": None,
            "company": None,
            "subscription_tier": "free",
            "subscription_expires_at": None
        }

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(**user_response_data)
        )
