'use client'

import { useState } from 'react'
import { X, Mail, Lock, User, Phone, Building } from 'lucide-react'
import { useAuth } from '../lib/contexts/AuthContext'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  initialMode?: 'login' | 'register'
}

export default function AuthModal({
  isOpen,
  onClose,
  initialMode = 'login'
}: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()

  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  })

  const [registerData, setRegisterData] = useState({
    email: '',
    name: '',
    password: '',
    confirmPassword: '',
    phone: '',
    company: ''
  })

  if (!isOpen) return null

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(loginData)
      onClose()
    } catch (err: any) {
      setError(err.message || '로그인에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 비밀번호 확인
    if (registerData.password !== registerData.confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }

    // 비밀번호 강도 검증
    if (registerData.password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.')
      return
    }

    setLoading(true)

    try {
      await register({
        email: registerData.email,
        name: registerData.name,
        password: registerData.password,
        phone: registerData.phone || undefined,
        company: registerData.company || undefined
      })
      onClose()
    } catch (err: any) {
      setError(err.message || '회원가입에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-md w-full p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X size={24} />
        </button>

        {/* Header */}
        <h2 className="text-2xl font-bold text-white mb-2">
          {mode === 'login' ? '로그인' : '회원가입'}
        </h2>
        <p className="text-gray-400 mb-6">
          {mode === 'login'
            ? 'OmniVibe Pro 계정으로 로그인하세요'
            : '새로운 계정을 생성하세요'}
        </p>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 mb-4">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Login Form */}
        {mode === 'login' && (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                이메일
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                  type="email"
                  value={loginData.email}
                  onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="your@email.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                비밀번호
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                  type="password"
                  value={loginData.password}
                  onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-medium py-2.5 rounded-lg transition"
            >
              {loading ? '로그인 중...' : '로그인'}
            </button>
          </form>
        )}

        {/* Register Form */}
        {mode === 'register' && (
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                이메일 *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                  type="email"
                  value={registerData.email}
                  onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="your@email.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                이름 *
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                  type="text"
                  value={registerData.name}
                  onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="홍길동"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                비밀번호 * (8자 이상)
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                  type="password"
                  value={registerData.password}
                  onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                비밀번호 확인 *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                  type="password"
                  value={registerData.confirmPassword}
                  onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  전화번호
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                  <input
                    type="tel"
                    value={registerData.phone}
                    onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                    placeholder="010-1234-5678"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  회사명
                </label>
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                  <input
                    type="text"
                    value={registerData.company}
                    onChange={(e) => setRegisterData({ ...registerData, company: e.target.value })}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-10 py-2.5 text-white focus:outline-none focus:border-blue-500"
                    placeholder="회사명"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-medium py-2.5 rounded-lg transition"
            >
              {loading ? '가입 중...' : '회원가입'}
            </button>
          </form>
        )}

        {/* Mode Toggle */}
        <div className="mt-6 text-center">
          <p className="text-gray-400">
            {mode === 'login' ? '계정이 없으신가요?' : '이미 계정이 있으신가요?'}
            {' '}
            <button
              onClick={() => {
                setMode(mode === 'login' ? 'register' : 'login')
                setError('')
              }}
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              {mode === 'login' ? '회원가입' : '로그인'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
