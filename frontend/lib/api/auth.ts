/**
 * Authentication API Client
 * 백엔드 인증 API와 통신하는 클라이언트
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const AUTH_ENDPOINT = `${API_URL}/api/v1/auth`;

// ==================== Types ====================

export interface UserCreate {
  email: string;
  name: string;
  password: string;
  phone?: string;
  company?: string;
}

export interface UserResponse {
  user_id: string;
  email: string;
  name: string;
  phone?: string;
  company?: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface APIKeyCreate {
  name: string;
  expires_in_days?: number;
}

export interface APIKeyCreateResponse {
  key_id: string;
  api_key: string;
  name: string;
  created_at: string;
  expires_at?: string;
}

export interface APIKeyResponse {
  key_id: string;
  name: string;
  key_preview: string;
  is_active: boolean;
  created_at: string;
  last_used?: string;
  expires_at?: string;
}

// ==================== Token Management ====================

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

export function getCurrentUser(): UserResponse | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

export function setCurrentUser(user: UserResponse): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('user', JSON.stringify(user));
}

// ==================== API Functions ====================

/**
 * 사용자 등록
 */
export async function register(userData: UserCreate): Promise<UserResponse> {
  const response = await fetch(`${AUTH_ENDPOINT}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

/**
 * 로그인
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${AUTH_ENDPOINT}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data: LoginResponse = await response.json();

  // 토큰과 사용자 정보 저장
  setTokens(data.access_token, data.refresh_token);
  setCurrentUser(data.user);

  return data;
}

/**
 * 로그아웃
 */
export async function logout(): Promise<void> {
  const token = getAccessToken();

  if (token) {
    try {
      await fetch(`${AUTH_ENDPOINT}/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  }

  // 로컬 토큰 삭제
  clearTokens();
}

/**
 * 토큰 갱신
 */
export async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    throw new Error('Token refresh failed');
  }

  const data: RefreshTokenResponse = await response.json();

  // 새 액세스 토큰 저장
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', data.access_token);
  }

  return data.access_token;
}

/**
 * 현재 사용자 정보 가져오기
 */
export async function getMe(): Promise<UserResponse> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    if (response.status === 401) {
      // 토큰 만료 시 갱신 시도
      const newToken = await refreshAccessToken();
      return getMe(); // 재시도
    }
    throw new Error('Failed to fetch user data');
  }

  const user = await response.json();
  setCurrentUser(user);
  return user;
}

/**
 * 사용자 정보 업데이트
 */
export async function updateMe(updates: Partial<UserCreate>): Promise<UserResponse> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/me`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Update failed');
  }

  const user = await response.json();
  setCurrentUser(user);
  return user;
}

/**
 * 비밀번호 변경
 */
export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/change-password`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Password change failed');
  }
}

/**
 * API 키 생성
 */
export async function createAPIKey(data: APIKeyCreate): Promise<APIKeyCreateResponse> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/api-keys`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API key creation failed');
  }

  return response.json();
}

/**
 * API 키 목록 가져오기
 */
export async function getAPIKeys(): Promise<APIKeyResponse[]> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/api-keys`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch API keys');
  }

  return response.json();
}

/**
 * API 키 삭제
 */
export async function deleteAPIKey(keyId: string): Promise<void> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const response = await fetch(`${AUTH_ENDPOINT}/api-keys/${keyId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API key deletion failed');
  }
}

/**
 * 인증된 fetch 래퍼
 * 자동으로 Authorization 헤더를 추가하고 401 시 토큰 갱신 시도
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('No access token');
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };

  let response = await fetch(url, { ...options, headers });

  // 401 시 토큰 갱신 후 재시도
  if (response.status === 401) {
    try {
      await refreshAccessToken();
      const newToken = getAccessToken();
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, { ...options, headers });
    } catch (error) {
      clearTokens();
      throw new Error('Authentication failed');
    }
  }

  return response;
}
