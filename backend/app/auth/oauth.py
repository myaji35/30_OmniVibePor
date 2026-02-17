"""
OAuth 2.0 인증 서비스 (Google)
"""
from typing import Optional, Dict
import httpx
from app.core.config import settings


class GoogleOAuth:
    """Google OAuth 2.0 인증"""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        self.authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Google OAuth 인증 URL 생성

        Args:
            state: CSRF 방지용 상태 토큰

        Returns:
            str: Google 로그인 페이지 URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_url}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """
        Authorization Code를 Access Token으로 교환

        Args:
            code: Google에서 발급한 Authorization Code

        Returns:
            dict: 토큰 정보 (access_token, refresh_token 등)
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)

            if response.status_code == 200:
                return response.json()

        return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Google Access Token으로 사용자 정보 조회

        Args:
            access_token: Google Access Token

        Returns:
            dict: 사용자 정보 (email, name, picture 등)
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.userinfo_url, headers=headers)

            if response.status_code == 200:
                return response.json()

        return None

    async def authenticate(self, code: str) -> Optional[Dict]:
        """
        Google OAuth 전체 인증 프로세스

        Args:
            code: Google Authorization Code

        Returns:
            dict: 사용자 정보
            {
                "email": "user@example.com",
                "name": "John Doe",
                "picture": "https://...",
                "google_id": "123456789",
                "verified_email": True
            }
        """
        # 1. Code를 Token으로 교환
        token_data = await self.exchange_code_for_token(code)
        if not token_data:
            return None

        access_token = token_data.get("access_token")
        if not access_token:
            return None

        # 2. Token으로 사용자 정보 조회
        user_info = await self.get_user_info(access_token)
        if not user_info:
            return None

        # 3. 사용자 정보 정규화
        return {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "google_id": user_info.get("id"),
            "verified_email": user_info.get("verified_email", False)
        }


# OAuth 인스턴스 싱글톤
google_oauth = GoogleOAuth()
