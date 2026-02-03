"use client";

import { useState } from "react";
import { X, Mail, Lock, User, Phone, Building } from "lucide-react";
import { useAuth } from "../lib/contexts/AuthContext";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: "login" | "register";
}

export default function AuthModal({
  isOpen,
  onClose,
  initialMode = "login",
}: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const [loginData, setLoginData] = useState({
    email: "",
    password: "",
  });

  const [registerData, setRegisterData] = useState({
    email: "",
    name: "",
    password: "",
    confirmPassword: "",
    phone: "",
    company: "",
  });

  if (!isOpen) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(loginData);
      onClose();
    } catch (err: any) {
      setError(err.message || "로그인에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (registerData.password !== registerData.confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }

    if (registerData.password.length < 8) {
      setError("비밀번호는 8자 이상이어야 합니다.");
      return;
    }

    setLoading(true);

    try {
      await register({
        email: registerData.email,
        name: registerData.name,
        password: registerData.password,
        phone: registerData.phone || undefined,
        company: registerData.company || undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || "회원가입에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-[#000]/90 backdrop-blur-[100px] flex items-center justify-center z-[100] p-4">
      {/* Background Aesthetic Blur for Modal */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-brand-primary-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="bg-[#0a0a0c] rounded-[3rem] border border-white/10 max-w-md w-full p-12 relative overflow-hidden shadow-2xl">
        {/* Glossy Reflection */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-8 right-8 w-10 h-10 bg-white/5 hover:bg-white/10 rounded-full flex items-center justify-center transition-all group"
        >
          <X className="w-5 h-5 text-gray-500 group-hover:text-white group-hover:rotate-90 transition-all duration-500" />
        </button>

        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-primary-500 shadow-[0_0_10px_#a855f7]" />
            <span className="text-[10px] font-black text-brand-primary-400 uppercase tracking-[0.4em]">
              Protocol Gateway
            </span>
          </div>
          <h2 className="text-3xl font-black font-outfit text-white tracking-tighter uppercase italic">
            {mode === "login" ? "Initialise Login" : "Create Identity"}
          </h2>
          <p className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mt-2">
            {mode === "login" ? "시스템 인증 프로세스 가동" : "새로운 엔진 사용자 등록"}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 mb-8 flex items-center gap-4 animate-shake">
            <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_#ef4444]" />
            <p className="text-red-400 text-[11px] font-black uppercase tracking-widest">
              {error}
            </p>
          </div>
        )}

        {/* Login Form */}
        {mode === "login" && (
          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-3">
              <label className="text-[10px] font-black text-gray-600 uppercase tracking-[0.3em] pl-1">
                Access Identifier (Email)
              </label>
              <div className="relative group">
                <Mail
                  className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-brand-primary-400 transition-colors"
                  size={18}
                />
                <input
                  type="email"
                  value={loginData.email}
                  onChange={(e) =>
                    setLoginData({ ...loginData, email: e.target.value })
                  }
                  className="w-full bg-white/[0.02] border border-white/5 group-hover:border-white/10 focus:border-brand-primary-500/50 rounded-2xl px-14 py-4 text-sm text-white focus:outline-none transition-all duration-500"
                  placeholder="name@corporation.com"
                  required
                />
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black text-gray-600 uppercase tracking-[0.3em] pl-1">
                Security Cipher (Password)
              </label>
              <div className="relative group">
                <Lock
                  className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-brand-primary-400 transition-colors"
                  size={18}
                />
                <input
                  type="password"
                  value={loginData.password}
                  onChange={(e) =>
                    setLoginData({ ...loginData, password: e.target.value })
                  }
                  className="w-full bg-white/[0.02] border border-white/5 group-hover:border-white/10 focus:border-brand-primary-500/50 rounded-2xl px-14 py-4 text-sm text-white focus:outline-none transition-all duration-500"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-5 bg-white text-black font-black text-[11px] uppercase tracking-[0.3em] rounded-2xl hover:bg-brand-primary-500 hover:text-white transition-all duration-500 shadow-2xl shadow-white/5 active:scale-95"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-3">
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  인증 확인 중...
                </div>
              ) : (
                "시스템 접속 시작 →"
              )}
            </button>
          </form>
        )}

        {/* Register Form */}
        {mode === "register" && (
          <form onSubmit={handleRegister} className="space-y-6">
            <div className="space-y-3">
              <label className="text-[10px] font-black text-gray-600 uppercase tracking-[0.3em] pl-1">
                Email Module
              </label>
              <div className="relative group">
                <Mail
                  className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-600"
                  size={18}
                />
                <input
                  type="email"
                  value={registerData.email}
                  onChange={(e) =>
                    setRegisterData({ ...registerData, email: e.target.value })
                  }
                  className="w-full bg-white/[0.02] border border-white/5 rounded-2xl px-14 py-4 text-sm text-white focus:outline-none focus:border-brand-primary-500/50 transition-all"
                  placeholder="your@email.com"
                  required
                />
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black text-gray-600 uppercase tracking-[0.3em] pl-1">
                Full Identity (Name)
              </label>
              <div className="relative group">
                <User
                  className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-600"
                  size={18}
                />
                <input
                  type="text"
                  value={registerData.name}
                  onChange={(e) =>
                    setRegisterData({ ...registerData, name: e.target.value })
                  }
                  className="w-full bg-white/[0.02] border border-white/5 rounded-2xl px-14 py-4 text-sm text-white focus:outline-none focus:border-brand-primary-500/50 transition-all"
                  placeholder="HONG GILDONG"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <label className="text-[9px] font-black text-gray-600 uppercase tracking-[0.3em] pl-1">
                  Cipher
                </label>
                <input
                  type="password"
                  value={registerData.password}
                  onChange={(e) =>
                    setRegisterData({
                      ...registerData,
                      password: e.target.value,
                    })
                  }
                  className="w-full bg-white/[0.02] border border-white/5 rounded-2xl px-5 py-4 text-sm text-white focus:outline-none focus:border-brand-primary-500/50 transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
              <div className="space-y-3">
                <label className="text-[9px] font-black text-gray-600 uppercase tracking-[0.3em] pl-1">
                  Verify
                </label>
                <input
                  type="password"
                  value={registerData.confirmPassword}
                  onChange={(e) =>
                    setRegisterData({
                      ...registerData,
                      confirmPassword: e.target.value,
                    })
                  }
                  className="w-full bg-white/[0.02] border border-white/5 rounded-2xl px-5 py-4 text-sm text-white focus:outline-none focus:border-brand-primary-500/50 transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-5 bg-white text-black font-black text-[11px] uppercase tracking-[0.3em] rounded-2xl hover:bg-brand-primary-500 hover:text-white transition-all duration-500 shadow-2xl shadow-white/5 active:scale-95"
            >
              {loading ? "데이터 생성 중..." : "사용자 프로토콜 등록 →"}
            </button>
          </form>
        )}

        {/* Mode Toggle & Auto-Pass Logic Feedback */}
        <div className="mt-10 flex flex-col items-center gap-6">
          <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">
            {mode === "login" ? "시스템 계정이 없으신가요?" : "이미 계정이 존재하시나요?"}
            <button
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError("");
              }}
              className="text-brand-primary-400 hover:text-white transition-colors ml-2 font-black"
            >
              {mode === "login" ? "지금 등록하기" : "비밀 인증 접속"}
            </button>
          </p>

          <div className="flex items-center gap-3 px-4 py-2 bg-emerald-500/5 border border-emerald-500/10 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[9px] font-black text-emerald-500/60 uppercase tracking-widest">
              Auto-Accept Passive Mode Active
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
