'use client'

import { useState } from 'react'

interface SheetStatus {
  available: boolean
  message: string
}

interface ConnectionResult {
  success: boolean
  spreadsheet_id?: string
  message: string
}

interface Strategy {
  [key: string]: string
}

interface ScheduleItem {
  [key: string]: string
}

interface GeneratedScript {
  campaign_name: string
  topic: string
  platform: string
  script: string
  hook?: string
  cta?: string
  estimated_duration?: number
  target_audience?: string
  tone?: string
}

interface Resource {
  캠페인명: string
  소제목: string
  리소스명: string
  리소스타입: string
  'URL/경로': string
  용도: string
  업로드일: string
}

type TabType = 'strategy' | 'schedule' | 'resources'

export default function SheetsPage() {
  const [sheetUrl, setSheetUrl] = useState('')
  const [sheetStatus, setSheetStatus] = useState<SheetStatus | null>(null)
  const [connectionResult, setConnectionResult] = useState<ConnectionResult | null>(null)
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [schedule, setSchedule] = useState<ScheduleItem[]>([])
  const [resources, setResources] = useState<Resource[]>([])
  const [activeTab, setActiveTab] = useState<TabType>('strategy')
  const [loading, setLoading] = useState(false)
  const [activeSpreadsheetId, setActiveSpreadsheetId] = useState<string | null>(null)
  const [generatedScript, setGeneratedScript] = useState<GeneratedScript | null>(null)
  const [generatingFor, setGeneratingFor] = useState<string | null>(null)

  // 시트 연결 상태 확인
  const checkStatus = async () => {
    try {
      const res = await fetch('/api/sheets-status')
      const data = await res.json()
      setSheetStatus(data)
    } catch (err) {
      console.error('상태 확인 실패:', err)
    }
  }

  // 구글 시트 연결
  const connectSheet = async () => {
    if (!sheetUrl.trim()) {
      alert('구글 시트 URL을 입력해주세요')
      return
    }

    setLoading(true)
    try {
      const res = await fetch('/api/sheets-connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ spreadsheet_url: sheetUrl })
      })

      const data = await res.json()
      setConnectionResult(data)

      if (data.success && data.spreadsheet_id) {
        setActiveSpreadsheetId(data.spreadsheet_id)

        // 연결 성공 시 시트 URL을 localStorage에 저장
        localStorage.setItem('connected_sheet_url', sheetUrl)
        localStorage.setItem('connected_spreadsheet_id', data.spreadsheet_id)
      }
    } catch (err) {
      console.error('연결 실패:', err)
      setConnectionResult({
        success: false,
        message: '연결 중 오류가 발생했습니다'
      })
    } finally {
      setLoading(false)
    }
  }

  // 전략 시트 불러오기
  const loadStrategy = async () => {
    if (!activeSpreadsheetId) {
      alert('먼저 시트를 연결해주세요')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`/api/sheets-strategy?spreadsheet_id=${activeSpreadsheetId}`)
      const data = await res.json()

      if (data.success) {
        setStrategy(data.strategy)
      }
    } catch (err) {
      console.error('전략 로드 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  // 스케줄 시트 불러오기
  const loadSchedule = async () => {
    if (!activeSpreadsheetId) {
      alert('먼저 시트를 연결해주세요')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`/api/sheets-schedule?spreadsheet_id=${activeSpreadsheetId}`)
      const data = await res.json()

      if (data.success) {
        setSchedule(data.schedule)
      }
    } catch (err) {
      console.error('스케줄 로드 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  // 리소스 시트 불러오기
  const loadResources = async () => {
    if (!activeSpreadsheetId) {
      alert('먼저 시트를 연결해주세요')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`/api/sheets-resources?spreadsheet_id=${activeSpreadsheetId}`)
      const data = await res.json()

      if (data.success) {
        setResources(data.resources)
      }
    } catch (err) {
      console.error('리소스 로드 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  // 스크립트 생성
  const generateScript = async (item: ScheduleItem) => {
    if (!activeSpreadsheetId) {
      alert('먼저 시트를 연결해주세요')
      return
    }

    const topic = item['소제목'] || item['주제']
    const campaignName = item['캠페인명']
    const platform = item['플랫폼'] || 'YouTube'

    setGeneratingFor(topic)
    try {
      const res = await fetch('/api/writer-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spreadsheet_id: activeSpreadsheetId,
          campaign_name: campaignName,
          topic: topic,
          platform: platform
        })
      })

      const data = await res.json()

      if (data.success) {
        setGeneratedScript(data)
      } else {
        alert(`스크립트 생성 실패: ${data.error || '알 수 없는 오류'}`)
      }
    } catch (err) {
      console.error('스크립트 생성 실패:', err)
      alert('스크립트 생성 중 오류가 발생했습니다')
    } finally {
      setGeneratingFor(null)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-16">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-blue-600">
            📊 구글 시트 연동
          </h1>
          <p className="text-xl text-gray-300">
            전략 및 콘텐츠 스케줄을 구글 시트로 관리하세요
          </p>
          <button
            onClick={checkStatus}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm"
          >
            연결 상태 확인
          </button>
        </div>

        {/* 상태 표시 */}
        {sheetStatus && (
          <div className={`max-w-2xl mx-auto mb-8 p-4 rounded-lg ${
            sheetStatus.available ? 'bg-green-500/20 border border-green-500/30' : 'bg-yellow-500/20 border border-yellow-500/30'
          }`}>
            <p className="text-center">
              {sheetStatus.available ? '✅ ' : '⚠️ '}
              {sheetStatus.message}
            </p>
          </div>
        )}

        {/* 시트 연결 */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
            <h2 className="text-2xl font-bold mb-4">시트 연결하기</h2>

            <div className="mb-4">
              <label className="block text-sm text-gray-300 mb-2">
                구글 시트 URL
              </label>
              <input
                type="text"
                value={sheetUrl}
                onChange={(e) => setSheetUrl(e.target.value)}
                placeholder="https://docs.google.com/spreadsheets/d/..."
                className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={connectSheet}
              disabled={loading}
              className="w-full px-6 py-3 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 rounded-lg font-semibold disabled:opacity-50"
            >
              {loading ? '연결 중...' : '시트 연결하기'}
            </button>

            {connectionResult && (
              <div className={`mt-4 p-4 rounded-lg ${
                connectionResult.success ? 'bg-green-500/20' : 'bg-red-500/20'
              }`}>
                <p>{connectionResult.success ? '✅' : '❌'} {connectionResult.message}</p>
                {connectionResult.spreadsheet_id && (
                  <p className="text-xs text-gray-400 mt-2">ID: {connectionResult.spreadsheet_id}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 탭 네비게이션 */}
        {activeSpreadsheetId && (
          <div className="max-w-6xl mx-auto mb-8">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-2 border border-white/20">
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setActiveTab('strategy')
                    if (strategy === null || Object.keys(strategy).length === 0) {
                      loadStrategy()
                    }
                  }}
                  className={`flex-1 px-6 py-4 rounded-xl transition-all ${
                    activeTab === 'strategy'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold'
                      : 'bg-white/5 hover:bg-white/10 text-gray-300'
                  }`}
                >
                  <h3 className="text-lg font-bold">📋 전략</h3>
                  <p className="text-xs mt-1 opacity-80">캠페인 전략 및 설정</p>
                </button>

                <button
                  onClick={() => {
                    setActiveTab('schedule')
                    if (schedule.length === 0) {
                      loadSchedule()
                    }
                  }}
                  className={`flex-1 px-6 py-4 rounded-xl transition-all ${
                    activeTab === 'schedule'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold'
                      : 'bg-white/5 hover:bg-white/10 text-gray-300'
                  }`}
                >
                  <h3 className="text-lg font-bold">📅 스케줄</h3>
                  <p className="text-xs mt-1 opacity-80">콘텐츠 일정 관리</p>
                </button>

                <button
                  onClick={() => {
                    setActiveTab('resources')
                    if (resources.length === 0) {
                      loadResources()
                    }
                  }}
                  className={`flex-1 px-6 py-4 rounded-xl transition-all ${
                    activeTab === 'resources'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold'
                      : 'bg-white/5 hover:bg-white/10 text-gray-300'
                  }`}
                >
                  <h3 className="text-lg font-bold">🎬 리소스</h3>
                  <p className="text-xs mt-1 opacity-80">이미지, 영상, 음원</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 탭 콘텐츠 */}
        {activeSpreadsheetId && (
          <>
            {/* 전략 탭 */}
            {activeTab === 'strategy' && strategy && Object.keys(strategy).length > 0 && (
              <div className="max-w-4xl mx-auto mb-8">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
                  <h2 className="text-2xl font-bold mb-4">📋 캠페인 전략</h2>
                  <div className="grid gap-3">
                    {Object.entries(strategy).map(([key, value]) => (
                      <div key={key} className="bg-white/5 rounded-lg p-4">
                        <p className="text-sm text-gray-400">{key}</p>
                        <p className="text-lg font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 스케줄 탭 */}
            {activeTab === 'schedule' && schedule.length > 0 && (
              <div className="max-w-6xl mx-auto mb-8">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
                  <h2 className="text-2xl font-bold mb-4">📅 콘텐츠 스케줄 ({schedule.length}개)</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/20">
                          {schedule[0] && Object.keys(schedule[0]).map((header) => (
                            <th key={header} className="px-4 py-3 text-left text-sm font-semibold">
                              {header}
                            </th>
                          ))}
                          <th className="px-4 py-3 text-left text-sm font-semibold">액션</th>
                        </tr>
                      </thead>
                      <tbody>
                        {schedule.map((item, idx) => (
                          <tr key={idx} className="border-b border-white/10 hover:bg-white/5">
                            {Object.values(item).map((value, i) => (
                              <td key={i} className="px-4 py-3 text-sm">
                                {value}
                              </td>
                            ))}
                            <td className="px-4 py-3">
                              <button
                                onClick={() => generateScript(item)}
                                disabled={generatingFor === (item['소제목'] || item['주제'])}
                                className="px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 rounded text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {generatingFor === (item['소제목'] || item['주제']) ? '생성 중...' : '📝 스크립트'}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* 리소스 탭 */}
            {activeTab === 'resources' && resources.length > 0 && (
              <div className="max-w-6xl mx-auto mb-8">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
                  <h2 className="text-2xl font-bold mb-4">🎬 리소스 목록 ({resources.length}개)</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/20">
                          <th className="px-4 py-3 text-left text-sm font-semibold">캠페인명</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">소제목</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">리소스명</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">타입</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">URL/경로</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">용도</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold">업로드일</th>
                        </tr>
                      </thead>
                      <tbody>
                        {resources.map((resource, idx) => (
                          <tr key={idx} className="border-b border-white/10 hover:bg-white/5">
                            <td className="px-4 py-3 text-sm">{resource.캠페인명}</td>
                            <td className="px-4 py-3 text-sm">{resource.소제목}</td>
                            <td className="px-4 py-3 text-sm font-semibold">{resource.리소스명}</td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                resource.리소스타입 === 'image' ? 'bg-blue-500/20 text-blue-400' :
                                resource.리소스타입 === 'video' ? 'bg-purple-500/20 text-purple-400' :
                                resource.리소스타입 === 'audio' ? 'bg-green-500/20 text-green-400' :
                                'bg-gray-500/20 text-gray-400'
                              }`}>
                                {resource.리소스타입}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <a href={resource['URL/경로']} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline truncate block max-w-xs">
                                {resource['URL/경로']}
                              </a>
                            </td>
                            <td className="px-4 py-3 text-sm">{resource.용도}</td>
                            <td className="px-4 py-3 text-sm text-gray-400">{resource.업로드일}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* 생성된 스크립트 표시 */}
        {generatedScript && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-lg rounded-2xl p-8 border border-purple-500/30">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold mb-2">✨ 생성된 스크립트</h2>
                  <p className="text-sm text-gray-300">
                    주제: {generatedScript.topic} | 플랫폼: {generatedScript.platform}
                  </p>
                </div>
                <button
                  onClick={() => setGeneratedScript(null)}
                  className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-sm"
                >
                  ✕ 닫기
                </button>
              </div>

              {/* 메타 정보 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {generatedScript.target_audience && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <p className="text-xs text-gray-400">타겟</p>
                    <p className="font-semibold">{generatedScript.target_audience}</p>
                  </div>
                )}
                {generatedScript.tone && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <p className="text-xs text-gray-400">톤앤매너</p>
                    <p className="font-semibold">{generatedScript.tone}</p>
                  </div>
                )}
                {generatedScript.estimated_duration && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <p className="text-xs text-gray-400">예상 길이</p>
                    <p className="font-semibold">{generatedScript.estimated_duration}초</p>
                  </div>
                )}
              </div>

              {/* 훅 */}
              {generatedScript.hook && (
                <div className="mb-6 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                  <h3 className="text-sm font-bold text-yellow-400 mb-2">🎣 훅 (첫 3초)</h3>
                  <p className="text-sm">{generatedScript.hook}</p>
                </div>
              )}

              {/* 본문 스크립트 */}
              <div className="mb-6 bg-white/5 rounded-lg p-4">
                <h3 className="text-sm font-bold mb-3">📝 스크립트 본문</h3>
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {generatedScript.script}
                </div>
              </div>

              {/* CTA */}
              {generatedScript.cta && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                  <h3 className="text-sm font-bold text-green-400 mb-2">📢 CTA (행동 유도)</h3>
                  <p className="text-sm">{generatedScript.cta}</p>
                </div>
              )}

              {/* 복사 버튼 */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(generatedScript.script)
                    alert('스크립트가 클립보드에 복사되었습니다!')
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold"
                >
                  📋 스크립트 복사
                </button>
                <button
                  onClick={() => {
                    const fullScript = `훅:\n${generatedScript.hook}\n\n본문:\n${generatedScript.script}\n\nCTA:\n${generatedScript.cta}`
                    navigator.clipboard.writeText(fullScript)
                    alert('전체 스크립트가 클립보드에 복사되었습니다!')
                  }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold"
                >
                  📄 전체 복사
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 홈으로 돌아가기 */}
        <div className="text-center mt-8">
          <a
            href="/"
            className="inline-block px-6 py-3 bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-lg border border-white/20 transition-all"
          >
            ← 홈으로 돌아가기
          </a>
        </div>
      </div>
    </main>
  )
}
