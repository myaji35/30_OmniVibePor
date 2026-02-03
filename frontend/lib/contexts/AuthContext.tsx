'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  UserResponse,
  LoginRequest,
  UserCreate,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  getMe,
  getCurrentUser,
  getAccessToken,
  clearTokens,
} from '../api/auth';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 초기 로드 시 토큰 확인
  useEffect(() => {
    const initAuth = async () => {
      const token = getAccessToken();
      const cachedUser = getCurrentUser();

      if (token && cachedUser) {
        setUser(cachedUser);

        // 백그라운드에서 사용자 정보 갱신
        try {
          const freshUser = await getMe();
          setUser(freshUser);
        } catch (error) {
          console.warn('Backend not available, using cached user:', error);
          // 백엔드가 없어도 캐시된 사용자 정보 유지
          // 토큰이 실제로 만료된 경우에만 clearTokens 호출
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const response = await apiLogin(credentials);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiLogout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: UserCreate) => {
    setIsLoading(true);
    try {
      await apiRegister(userData);
      // 등록 후 자동 로그인
      await login({ email: userData.email, password: userData.password });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const freshUser = await getMe();
      setUser(freshUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      clearTokens();
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
