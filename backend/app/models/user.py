"""사용자 인증 및 권한 모델"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
import uuid
import re


class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(BaseModel):
    """사용자 모델"""
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # 프로필 정보
    profile_image_url: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None

    # 구독 정보 (기존 SubscriptionTier와 연동)
    subscription_tier: str = "free"
    subscription_expires_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('phone')
    def validate_phone(cls, v):
        """전화번호 형식 검증"""
        if v and not re.match(r'^\+?1?\d{9,15}$', v.replace('-', '').replace(' ', '')):
            raise ValueError('Invalid phone number format')
        return v


class UserCreate(BaseModel):
    """사용자 생성 요청"""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = None
    company: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """사용자 정보 업데이트 요청"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    company: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserPasswordChange(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserResponse(BaseModel):
    """사용자 응답 (비밀번호 제외)"""
    user_id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    profile_image_url: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    subscription_tier: str
    subscription_expires_at: Optional[datetime]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """로그인 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30분 (초 단위)
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """토큰 갱신 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class APIKey(BaseModel):
    """API 키 모델"""
    key_id: str = Field(default_factory=lambda: f"key_{uuid.uuid4().hex[:12]}")
    user_id: str
    name: str = Field(..., min_length=1, max_length=100, description="API 키 이름")
    key_hash: str = Field(..., description="해시된 API 키")
    prefix: str = Field(..., description="API 키 프리픽스 (표시용)")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # 사용량 추적
    usage_count: int = 0
    rate_limit: int = 1000  # 시간당 요청 제한

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIKeyCreate(BaseModel):
    """API 키 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    rate_limit: int = Field(1000, ge=1, le=10000)


class APIKeyResponse(BaseModel):
    """API 키 응답"""
    key_id: str
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    usage_count: int
    rate_limit: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIKeyCreateResponse(BaseModel):
    """API 키 생성 응답 (실제 키 포함)"""
    key_id: str
    name: str
    api_key: str  # 실제 API 키 (생성 시 1회만 반환)
    prefix: str
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== Neo4j CRUD Extensions ====================

class UserCRUD:
    """사용자 CRUD 작업 (Neo4j)"""

    def __init__(self, neo4j_client):
        self.client = neo4j_client

    def create_user(self, user: User) -> Dict:
        """사용자 생성"""
        query = """
        CREATE (u:User {
            user_id: $user_id,
            email: $email,
            name: $name,
            hashed_password: $hashed_password,
            role: $role,
            is_active: $is_active,
            is_verified: $is_verified,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            last_login: datetime($last_login),
            profile_image_url: $profile_image_url,
            phone: $phone,
            company: $company,
            subscription_tier: $subscription_tier,
            subscription_expires_at: datetime($subscription_expires_at)
        })
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.role as role,
               u.is_active as is_active,
               u.is_verified as is_verified,
               u.created_at as created_at
        """

        params = user.model_dump()
        # datetime 객체를 ISO 형식 문자열로 변환
        if params.get('created_at'):
            params['created_at'] = params['created_at'].isoformat()
        if params.get('updated_at'):
            params['updated_at'] = params['updated_at'].isoformat()
        if params.get('last_login'):
            params['last_login'] = params['last_login'].isoformat()
        if params.get('subscription_expires_at'):
            params['subscription_expires_at'] = params['subscription_expires_at'].isoformat()

        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 조회"""
        query = """
        MATCH (u:User {email: $email})
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.hashed_password as hashed_password,
               u.role as role,
               u.is_active as is_active,
               u.is_verified as is_verified,
               u.created_at as created_at,
               u.updated_at as updated_at,
               u.last_login as last_login,
               u.profile_image_url as profile_image_url,
               u.phone as phone,
               u.company as company,
               u.subscription_tier as subscription_tier,
               u.subscription_expires_at as subscription_expires_at
        """
        result = self.client.query(query, {"email": email})
        if result:
            row = result[0]
            # Neo4j DateTime을 Python datetime으로 변환
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            if row.get('last_login'):
                row['last_login'] = row['last_login'].to_native()
            if row.get('subscription_expires_at'):
                row['subscription_expires_at'] = row['subscription_expires_at'].to_native()
            return row
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """ID로 사용자 조회"""
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.hashed_password as hashed_password,
               u.role as role,
               u.is_active as is_active,
               u.is_verified as is_verified,
               u.created_at as created_at,
               u.updated_at as updated_at,
               u.last_login as last_login,
               u.profile_image_url as profile_image_url,
               u.phone as phone,
               u.company as company,
               u.subscription_tier as subscription_tier,
               u.subscription_expires_at as subscription_expires_at
        """
        result = self.client.query(query, {"user_id": user_id})
        if result:
            row = result[0]
            # Neo4j DateTime을 Python datetime으로 변환
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            if row.get('last_login'):
                row['last_login'] = row['last_login'].to_native()
            if row.get('subscription_expires_at'):
                row['subscription_expires_at'] = row['subscription_expires_at'].to_native()
            return row
        return None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트"""
        # updated_at 자동 추가
        updates['updated_at'] = datetime.utcnow().isoformat()

        set_clauses = [f"u.{key} = ${key}" for key in updates.keys()]
        query = f"""
        MATCH (u:User {{user_id: $user_id}})
        SET {", ".join(set_clauses)}
        RETURN u.user_id as user_id
        """
        params = {"user_id": user_id, **updates}
        result = self.client.query(query, params)
        return len(result) > 0

    def update_last_login(self, user_id: str) -> bool:
        """마지막 로그인 시간 업데이트"""
        query = """
        MATCH (u:User {user_id: $user_id})
        SET u.last_login = datetime()
        RETURN u.user_id as user_id
        """
        result = self.client.query(query, {"user_id": user_id})
        return len(result) > 0

    def delete_user(self, user_id: str) -> bool:
        """사용자 삭제"""
        query = """
        MATCH (u:User {user_id: $user_id})
        DETACH DELETE u
        RETURN count(u) as deleted_count
        """
        result = self.client.query(query, {"user_id": user_id})
        return result[0]["deleted_count"] > 0 if result else False

    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict]:
        """사용자 목록 조회"""
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if role:
            where_clauses.append("u.role = $role")
            params["role"] = role.value

        if is_active is not None:
            where_clauses.append("u.is_active = $is_active")
            params["is_active"] = is_active

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
        MATCH (u:User)
        {where_clause}
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.role as role,
               u.is_active as is_active,
               u.is_verified as is_verified,
               u.created_at as created_at,
               u.updated_at as updated_at,
               u.last_login as last_login,
               u.subscription_tier as subscription_tier
        ORDER BY u.created_at DESC
        SKIP $skip
        LIMIT $limit
        """

        results = self.client.query(query, params)
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            if row.get('last_login'):
                row['last_login'] = row['last_login'].to_native()
        return results


class APIKeyCRUD:
    """API 키 CRUD 작업 (Neo4j)"""

    def __init__(self, neo4j_client):
        self.client = neo4j_client

    def create_api_key(self, api_key: APIKey) -> Dict:
        """API 키 생성"""
        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (k:APIKey {
            key_id: $key_id,
            name: $name,
            key_hash: $key_hash,
            prefix: $prefix,
            is_active: $is_active,
            created_at: datetime($created_at),
            last_used_at: datetime($last_used_at),
            expires_at: datetime($expires_at),
            usage_count: $usage_count,
            rate_limit: $rate_limit
        })
        CREATE (u)-[:HAS_API_KEY]->(k)
        RETURN k.key_id as key_id,
               k.name as name,
               k.prefix as prefix,
               k.created_at as created_at
        """

        params = api_key.model_dump()
        if params.get('created_at'):
            params['created_at'] = params['created_at'].isoformat()
        if params.get('last_used_at'):
            params['last_used_at'] = params['last_used_at'].isoformat() if params['last_used_at'] else None
        if params.get('expires_at'):
            params['expires_at'] = params['expires_at'].isoformat() if params['expires_at'] else None

        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict]:
        """해시로 API 키 조회"""
        query = """
        MATCH (u:User)-[:HAS_API_KEY]->(k:APIKey {key_hash: $key_hash})
        RETURN k.key_id as key_id,
               k.name as name,
               k.key_hash as key_hash,
               k.prefix as prefix,
               k.is_active as is_active,
               k.created_at as created_at,
               k.last_used_at as last_used_at,
               k.expires_at as expires_at,
               k.usage_count as usage_count,
               k.rate_limit as rate_limit,
               u.user_id as user_id
        """
        result = self.client.query(query, {"key_hash": key_hash})
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('last_used_at'):
                row['last_used_at'] = row['last_used_at'].to_native()
            if row.get('expires_at'):
                row['expires_at'] = row['expires_at'].to_native()
            return row
        return None

    def list_user_api_keys(self, user_id: str) -> List[Dict]:
        """사용자의 API 키 목록 조회"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_API_KEY]->(k:APIKey)
        RETURN k.key_id as key_id,
               k.name as name,
               k.prefix as prefix,
               k.is_active as is_active,
               k.created_at as created_at,
               k.last_used_at as last_used_at,
               k.expires_at as expires_at,
               k.usage_count as usage_count,
               k.rate_limit as rate_limit
        ORDER BY k.created_at DESC
        """
        results = self.client.query(query, {"user_id": user_id})
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('last_used_at'):
                row['last_used_at'] = row['last_used_at'].to_native()
            if row.get('expires_at'):
                row['expires_at'] = row['expires_at'].to_native()
        return results

    def update_api_key_usage(self, key_id: str) -> bool:
        """API 키 사용 기록 업데이트"""
        query = """
        MATCH (k:APIKey {key_id: $key_id})
        SET k.usage_count = k.usage_count + 1,
            k.last_used_at = datetime()
        RETURN k.key_id as key_id
        """
        result = self.client.query(query, {"key_id": key_id})
        return len(result) > 0

    def revoke_api_key(self, key_id: str) -> bool:
        """API 키 비활성화"""
        query = """
        MATCH (k:APIKey {key_id: $key_id})
        SET k.is_active = false
        RETURN k.key_id as key_id
        """
        result = self.client.query(query, {"key_id": key_id})
        return len(result) > 0

    def delete_api_key(self, key_id: str) -> bool:
        """API 키 삭제"""
        query = """
        MATCH (k:APIKey {key_id: $key_id})
        DETACH DELETE k
        RETURN count(k) as deleted_count
        """
        result = self.client.query(query, {"key_id": key_id})
        return result[0]["deleted_count"] > 0 if result else False
