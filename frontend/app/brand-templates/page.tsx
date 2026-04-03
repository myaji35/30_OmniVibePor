'use client'

/**
 * 브랜드 템플릿 관리 페이지
 * ISS-027: 인트로/아웃트로 스크립트 편집, 음성 설정, 기본 템플릿 지정
 */

import { useState, useCallback, useEffect } from 'react'
import {
  Settings, Plus, Trash2, Star, Save, ChevronDown, ChevronUp,
  Loader2, Mic, Film, Type, Palette, Clock,
} from 'lucide-react'
import AppShell from '@/components/AppShell'

interface IntroConfig {
  enabled: boolean
  duration: number
  script: string
  background_color: string
  title_template: string
  subtitle_template: string
}

interface OutroConfig {
  enabled: boolean
  duration: number
  script: string
  cta_text: string
  contact_info: string
}

interface VoiceConfig {
  voice_id: string
  speed: number
  engine: string
}

interface BrandTemplate {
  id: string
  project_id: string
  name: string
  is_default: boolean
  intro: IntroConfig
  outro: OutroConfig
  voice_config: VoiceConfig
  created_at: string
  updated_at: string
}

const DEFAULT_INTRO: IntroConfig = {
  enabled: true, duration: 3, script: '',
  background_color: '#16325C', title_template: '{{presentation_title}}',
  subtitle_template: '{{date}} | {{author}}',
}

const DEFAULT_OUTRO: OutroConfig = {
  enabled: true, duration: 4, script: '',
  cta_text: '구독 · 좋아요 · 공유', contact_info: '',
}

const DEFAULT_VOICE: VoiceConfig = {
  voice_id: 'onyx', speed: 1.0, engine: 'openai',
}

const VOICE_OPTIONS = [
  { id: 'alloy', label: 'Alloy (중성)' },
  { id: 'echo', label: 'Echo (남성)' },
  { id: 'fable', label: 'Fable (���국)' },
  { id: 'onyx', label: 'Onyx (남성, 깊은)' },
  { id: 'nova', label: 'Nova (여성)' },
  { id: 'shimmer', label: 'Shimmer (여성, 따뜻)' },
]

const PROJECT_ID = 'default'

export default function BrandTemplatesPage() {
  const [templates, setTemplates] = useState<BrandTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [editData, setEditData] = useState<Partial<BrandTemplate> | null>(null)
  const [showNew, setShowNew] = useState(false)
  const [newName, setNewName] = useState('')
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/brand-templates?project_id=${PROJECT_ID}`)
      const data = await res.json()
      setTemplates(data.templates || [])
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  useEffect(() => { fetchTemplates() }, [fetchTemplates])

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleCreate = async () => {
    if (!newName.trim()) return
    setSaving(true)
    try {
      const res = await fetch('/api/brand-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: PROJECT_ID, name: newName.trim(),
          intro: DEFAULT_INTRO, outro: DEFAULT_OUTRO, voice_config: DEFAULT_VOICE,
        }),
      })
      if (res.ok) {
        showMessage('템플릿이 생성되었습니다', 'success')
        setNewName('')
        setShowNew(false)
        fetchTemplates()
      }
    } catch { showMessage('생성 실패', 'error') }
    setSaving(false)
  }

  const handleSave = async (tpl: BrandTemplate) => {
    if (!editData) return
    setSaving(true)
    try {
      const res = await fetch(`/api/brand-templates?id=${tpl.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editData),
      })
      if (res.ok) {
        showMessage('저장되었습니다', 'success')
        setEditData(null)
        fetchTemplates()
      }
    } catch { showMessage('저장 실패', 'error') }
    setSaving(false)
  }

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/brand-templates?id=${id}`, { method: 'DELETE' })
      showMessage('삭제되었습니다', 'success')
      if (expandedId === id) { setExpandedId(null); setEditData(null) }
      fetchTemplates()
    } catch { showMessage('삭제 실패', 'error') }
  }

  const handleSetDefault = async (id: string) => {
    try {
      await fetch(`/api/brand-templates?id=${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_default: true }),
      })
      showMessage('기본 템플릿으로 설정되었습니다', 'success')
      fetchTemplates()
    } catch { showMessage('설정 실패', 'error') }
  }

  const startEdit = (tpl: BrandTemplate) => {
    setExpandedId(tpl.id)
    setEditData({ name: tpl.name, intro: { ...tpl.intro }, outro: { ...tpl.outro }, voice_config: { ...tpl.voice_config } })
  }

  const updateIntro = (key: keyof IntroConfig, value: unknown) => {
    if (!editData) return
    setEditData({ ...editData, intro: { ...(editData.intro || DEFAULT_INTRO), [key]: value } as IntroConfig })
  }

  const updateOutro = (key: keyof OutroConfig, value: unknown) => {
    if (!editData) return
    setEditData({ ...editData, outro: { ...(editData.outro || DEFAULT_OUTRO), [key]: value } as OutroConfig })
  }

  const updateVoice = (key: keyof VoiceConfig, value: unknown) => {
    if (!editData) return
    setEditData({ ...editData, voice_config: { ...(editData.voice_config || DEFAULT_VOICE), [key]: value } as VoiceConfig })
  }

  return (
    <AppShell title="브랜드 템플릿">
      <div className="max-w-4xl mx-auto py-8 px-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#6366F1]/10 flex items-center justify-center">
              <Settings className="w-5 h-5 text-[#6366F1]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">브랜드 템플릿</h1>
              <p className="text-sm text-white/40">인트로/아웃트로 · 음성 설정 · 기본 템플릿 관리</p>
            </div>
          </div>
          <button onClick={() => setShowNew(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold bg-[#6366F1] text-white hover:bg-[#5558E6] transition-all">
            <Plus className="w-4 h-4" /> 새 템플릿
          </button>
        </div>

        {/* 메시지 */}
        {message && (
          <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm font-semibold ${message.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
            {message.text}
          </div>
        )}

        {/* 새 템플릿 입력 */}
        {showNew && (
          <div className="mb-6 rounded-xl bg-[#141414] border border-[#6366F1]/30 p-5">
            <div className="flex items-center gap-3">
              <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="템플릿 이름 (예: 기업 프레젠테이션)"
                className="flex-1 px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]"
                onKeyDown={e => e.key === 'Enter' && handleCreate()} />
              <button onClick={handleCreate} disabled={saving || !newName.trim()}
                className="px-4 py-2.5 rounded-lg text-sm font-bold bg-[#6366F1] text-white disabled:opacity-50">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : '생성'}
              </button>
              <button onClick={() => { setShowNew(false); setNewName('') }}
                className="px-3 py-2.5 rounded-lg text-sm text-white/40 hover:text-white/70">취소</button>
            </div>
          </div>
        )}

        {/* 로딩 */}
        {loading ? (
          <div className="h-40 flex items-center justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-white/20" />
          </div>
        ) : templates.length === 0 ? (
          <div className="h-40 flex flex-col items-center justify-center text-white/20 gap-2">
            <Settings className="w-8 h-8" />
            <span className="text-sm">아직 템플릿이 없습니다</span>
            <button onClick={() => setShowNew(true)} className="mt-2 text-xs text-[#6366F1] hover:text-[#8183F4]">+ 첫 템플릿 만들기</button>
          </div>
        ) : (
          <div className="space-y-3">
            {templates.map(tpl => {
              const isExpanded = expandedId === tpl.id
              const intro = editData && isExpanded ? (editData.intro || tpl.intro) : tpl.intro
              const outro = editData && isExpanded ? (editData.outro || tpl.outro) : tpl.outro
              const voice = editData && isExpanded ? (editData.voice_config || tpl.voice_config) : tpl.voice_config

              return (
                <div key={tpl.id} className={`rounded-xl bg-[#141414] border transition-all ${isExpanded ? 'border-[#6366F1]/40' : 'border-white/[0.07]'}`}>
                  {/* 카드 헤더 */}
                  <div className="flex items-center gap-3 px-5 py-4 cursor-pointer" onClick={() => isExpanded ? (setExpandedId(null), setEditData(null)) : startEdit(tpl)}>
                    <Film className="w-4 h-4 text-[#6366F1]" />
                    <span className="text-sm font-bold text-white flex-1">{tpl.name}</span>
                    {tpl.is_default && (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F59E0B] text-white">
                        <Star className="w-3 h-3" /> 기본
                      </span>
                    )}
                    <span className="text-[10px] text-white/20 font-mono">{tpl.id}</span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-white/30" /> : <ChevronDown className="w-4 h-4 text-white/30" />}
                  </div>

                  {/* 확장된 편집 영역 */}
                  {isExpanded && editData && (
                    <div className="px-5 pb-5 space-y-5 border-t border-white/[0.05]">
                      {/* 이름 */}
                      <div className="pt-4">
                        <label className="block text-xs font-semibold text-gray-400 mb-1.5">템플릿 이름</label>
                        <input value={editData.name || ''} onChange={e => setEditData({ ...editData, name: e.target.value })}
                          className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
                      </div>

                      {/* ── 인트로 설정 ── */}
                      <div className="rounded-lg border border-white/[0.05] p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Type className="w-3.5 h-3.5 text-[#A855F7]" />
                            <span className="text-xs font-bold text-white/60">인트로</span>
                          </div>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={intro.enabled} onChange={e => updateIntro('enabled', e.target.checked)}
                              className="w-3.5 h-3.5 rounded accent-[#6366F1]" />
                            <span className="text-[10px] text-white/40">활성화</span>
                          </label>
                        </div>
                        {intro.enabled && (
                          <>
                            <div>
                              <label className="block text-[10px] text-white/30 mb-1">나레이션 스크립트</label>
                              <textarea value={intro.script} onChange={e => updateIntro('script', e.target.value)} rows={3}
                                placeholder="안녕하세요, {{presentation_title}} 발표를 시작하겠습니다."
                                className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] resize-none" />
                            </div>
                            <div className="grid grid-cols-3 gap-3">
                              <div>
                                <label className="block text-[10px] text-white/30 mb-1">
                                  <Clock className="w-3 h-3 inline mr-1" />길이 (초)
                                </label>
                                <input type="number" min={0.5} max={30} step={0.5} value={intro.duration}
                                  onChange={e => updateIntro('duration', Number(e.target.value))}
                                  className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                              </div>
                              <div>
                                <label className="block text-[10px] text-white/30 mb-1">
                                  <Palette className="w-3 h-3 inline mr-1" />배경 색상
                                </label>
                                <div className="flex items-center gap-2">
                                  <input type="color" value={intro.background_color} onChange={e => updateIntro('background_color', e.target.value)}
                                    className="w-8 h-8 rounded cursor-pointer border-0 bg-transparent" />
                                  <input value={intro.background_color} onChange={e => updateIntro('background_color', e.target.value)}
                                    className="flex-1 px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1] font-mono" />
                                </div>
                              </div>
                              <div>
                                <label className="block text-[10px] text-white/30 mb-1">제목 템플릿</label>
                                <input value={intro.title_template} onChange={e => updateIntro('title_template', e.target.value)}
                                  className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                              </div>
                            </div>
                          </>
                        )}
                      </div>

                      {/* ── 아웃트로 설정 ── */}
                      <div className="rounded-lg border border-white/[0.05] p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Type className="w-3.5 h-3.5 text-[#22C55E]" />
                            <span className="text-xs font-bold text-white/60">아웃트로</span>
                          </div>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={outro.enabled} onChange={e => updateOutro('enabled', e.target.checked)}
                              className="w-3.5 h-3.5 rounded accent-[#6366F1]" />
                            <span className="text-[10px] text-white/40">활성화</span>
                          </label>
                        </div>
                        {outro.enabled && (
                          <>
                            <div>
                              <label className="block text-[10px] text-white/30 mb-1">나레이션 스크립트</label>
                              <textarea value={outro.script} onChange={e => updateOutro('script', e.target.value)} rows={3}
                                placeholder="시청해 주셔서 감사합니다. 다음 영상도 기대해 주세요!"
                                className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] resize-none" />
                            </div>
                            <div className="grid grid-cols-3 gap-3">
                              <div>
                                <label className="block text-[10px] text-white/30 mb-1">
                                  <Clock className="w-3 h-3 inline mr-1" />길이 (초)
                                </label>
                                <input type="number" min={0.5} max={30} step={0.5} value={outro.duration}
                                  onChange={e => updateOutro('duration', Number(e.target.value))}
                                  className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                              </div>
                              <div>
                                <label className="block text-[10px] text-white/30 mb-1">CTA 텍스트</label>
                                <input value={outro.cta_text} onChange={e => updateOutro('cta_text', e.target.value)}
                                  className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                              </div>
                              <div>
                                <label className="block text-[10px] text-white/30 mb-1">연락처</label>
                                <input value={outro.contact_info} onChange={e => updateOutro('contact_info', e.target.value)}
                                  placeholder="hello@company.com"
                                  className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                              </div>
                            </div>
                          </>
                        )}
                      </div>

                      {/* ── 음성 설정 ── */}
                      <div className="rounded-lg border border-white/[0.05] p-4 space-y-3">
                        <div className="flex items-center gap-2">
                          <Mic className="w-3.5 h-3.5 text-[#3B82F6]" />
                          <span className="text-xs font-bold text-white/60">음성 설정</span>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="block text-[10px] text-white/30 mb-1">음성</label>
                            <select value={voice.voice_id} onChange={e => updateVoice('voice_id', e.target.value)}
                              className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-[#141414] focus:outline-none focus:border-[#6366F1]">
                              {VOICE_OPTIONS.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
                            </select>
                          </div>
                          <div>
                            <label className="block text-[10px] text-white/30 mb-1">속도 ({voice.speed}x)</label>
                            <input type="range" min={0.5} max={2} step={0.1} value={voice.speed}
                              onChange={e => updateVoice('speed', Number(e.target.value))}
                              className="w-full accent-[#6366F1]" />
                          </div>
                          <div>
                            <label className="block text-[10px] text-white/30 mb-1">엔진</label>
                            <select value={voice.engine} onChange={e => updateVoice('engine', e.target.value)}
                              className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-[#141414] focus:outline-none focus:border-[#6366F1]">
                              <option value="openai">OpenAI TTS</option>
                              <option value="elevenlabs">ElevenLabs</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* 액션 버튼 */}
                      <div className="flex items-center gap-3 pt-2">
                        <button onClick={() => handleSave(tpl)} disabled={saving}
                          className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold bg-[#6366F1] text-white hover:bg-[#5558E6] disabled:opacity-50 transition-all">
                          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} 저장
                        </button>
                        {!tpl.is_default && (
                          <button onClick={() => handleSetDefault(tpl.id)}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/20 hover:bg-[#F59E0B]/20 transition-all">
                            <Star className="w-4 h-4" /> 기본으로 설정
                          </button>
                        )}
                        <button onClick={() => handleDelete(tpl.id)}
                          className="ml-auto flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-red-400/60 hover:text-red-400 hover:bg-red-500/10 transition-all">
                          <Trash2 className="w-4 h-4" /> 삭제
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* 변수 안내 */}
        <div className="mt-8 rounded-xl bg-white/[0.02] border border-white/[0.05] p-4">
          <h3 className="text-xs font-bold text-white/40 mb-2">사용 가능한 변수</h3>
          <div className="grid grid-cols-2 gap-2 text-[11px] text-white/30">
            <span><code className="text-[#6366F1]">{'{{presentation_title}}'}</code> — 발표 제목</span>
            <span><code className="text-[#6366F1]">{'{{author}}'}</code> — 발표자 이름</span>
            <span><code className="text-[#6366F1]">{'{{date}}'}</code> — 생성 날짜</span>
            <span><code className="text-[#6366F1]">{'{{slide_count}}'}</code> — 슬라이드 수</span>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
