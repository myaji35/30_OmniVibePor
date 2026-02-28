'use client'

import { useState, useEffect } from 'react'
import AppShell from '@/components/AppShell'

interface ContentSchedule {
  id: number
  '소제목': string
  '캠페인명': string
  '플랫폼': string
  '발행일': string
  '주제': string
  '상태': string
}

interface ApiResponse {
  success: boolean
  schedule: ContentSchedule[]
  count: number
  total: number
  page: number
  limit: number
  totalPages: number
  filters: {
    search: string
    platform: string
    status: string
    campaign_id: string
  }
}

interface Toast {
  type: 'success' | 'error' | 'info'
  message: string
}

export default function SchedulePage() {
  // Data state
  const [schedules, setSchedules] = useState<ContentSchedule[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [platformFilter, setPlatformFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateRangeStart, setDateRangeStart] = useState('')
  const [dateRangeEnd, setDateRangeEnd] = useState('')

  // Sort state
  const [sortBy, setSortBy] = useState<'publish_date' | 'created_at'>('publish_date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // UI state
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingItem, setEditingItem] = useState<ContentSchedule | null>(null)

  // Form state for Create/Edit
  const [formData, setFormData] = useState({
    campaign_id: 1,
    topic: '',
    subtitle: '',
    platform: 'Youtube',
    publish_date: '',
    status: 'draft',
    target_audience: '',
    keywords: '',
    notes: ''
  })

  // Load data
  useEffect(() => {
    loadSchedules()
  }, [currentPage, itemsPerPage, searchQuery, platformFilter, statusFilter, sortBy, sortOrder])

  const loadSchedules = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: itemsPerPage.toString(),
        ...(searchQuery && { search: searchQuery }),
        ...(platformFilter && { platform: platformFilter }),
        ...(statusFilter && { status: statusFilter })
      })

      const res = await fetch(`/api/sheets-schedule?${params}`)
      const data: ApiResponse = await res.json()

      if (data.success) {
        setSchedules(data.schedule)
        setTotalCount(data.total)
        setTotalPages(data.totalPages)
      } else {
        showToast('error', '데이터 로드 실패')
      }
    } catch (error) {
      console.error('Load error:', error)
      showToast('error', '데이터 로드 중 오류 발생')
    } finally {
      setLoading(false)
    }
  }

  // Toast notification
  const showToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3000)
  }

  // Create schedule
  const createSchedule = async () => {
    if (!formData.topic || !formData.subtitle) {
      showToast('error', '필수 필드를 입력해주세요')
      return
    }

    setLoading(true)
    try {
      const res = await fetch('/api/sheets-schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      const data = await res.json()

      if (data.success) {
        showToast('success', '스케줄이 생성되었습니다')
        setShowCreateModal(false)
        resetForm()
        loadSchedules()
      } else {
        showToast('error', data.error || '생성 실패')
      }
    } catch (error) {
      console.error('Create error:', error)
      showToast('error', '생성 중 오류 발생')
    } finally {
      setLoading(false)
    }
  }

  // Update schedule
  const updateSchedule = async () => {
    if (!editingItem) return

    setLoading(true)
    try {
      const res = await fetch('/api/sheets-schedule', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: editingItem.id,
          ...formData
        })
      })

      const data = await res.json()

      if (data.success) {
        showToast('success', '스케줄이 수정되었습니다')
        setShowEditModal(false)
        setEditingItem(null)
        resetForm()
        loadSchedules()
      } else {
        showToast('error', data.error || '수정 실패')
      }
    } catch (error) {
      console.error('Update error:', error)
      showToast('error', '수정 중 오류 발생')
    } finally {
      setLoading(false)
    }
  }

  // Delete schedule
  const deleteSchedule = async (id: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return

    setLoading(true)
    try {
      const res = await fetch(`/api/sheets-schedule?id=${id}`, {
        method: 'DELETE'
      })

      const data = await res.json()

      if (data.success) {
        showToast('success', '스케줄이 삭제되었습니다')
        loadSchedules()
      } else {
        showToast('error', data.error || '삭제 실패')
      }
    } catch (error) {
      console.error('Delete error:', error)
      showToast('error', '삭제 중 오류 발생')
    } finally {
      setLoading(false)
    }
  }

  // Bulk delete
  const bulkDelete = async () => {
    if (selectedIds.length === 0) {
      showToast('info', '선택된 항목이 없습니다')
      return
    }

    if (!confirm(`${selectedIds.length}개 항목을 삭제하시겠습니까?`)) return

    setLoading(true)
    try {
      await Promise.all(
        selectedIds.map(id =>
          fetch(`/api/sheets-schedule?id=${id}`, { method: 'DELETE' })
        )
      )

      showToast('success', `${selectedIds.length}개 항목이 삭제되었습니다`)
      setSelectedIds([])
      loadSchedules()
    } catch (error) {
      console.error('Bulk delete error:', error)
      showToast('error', '일괄 삭제 중 오류 발생')
    } finally {
      setLoading(false)
    }
  }

  // Bulk status update
  const bulkUpdateStatus = async (newStatus: string) => {
    if (selectedIds.length === 0) {
      showToast('info', '선택된 항목이 없습니다')
      return
    }

    setLoading(true)
    try {
      await Promise.all(
        selectedIds.map(id =>
          fetch('/api/sheets-schedule', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, status: newStatus })
          })
        )
      )

      showToast('success', `${selectedIds.length}개 항목의 상태가 변경되었습니다`)
      setSelectedIds([])
      loadSchedules()
    } catch (error) {
      console.error('Bulk update error:', error)
      showToast('error', '일괄 수정 중 오류 발생')
    } finally {
      setLoading(false)
    }
  }

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['ID', '소제목', '캠페인명', '플랫폼', '발행일', '주제', '상태']
    const rows = schedules.map(item => [
      item.id,
      item['소제목'],
      item['캠페인명'],
      item['플랫폼'],
      item['발행일'],
      item['주제'],
      item['상태']
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `content_schedule_${new Date().toISOString().split('T')[0]}.csv`
    link.click()

    showToast('success', 'CSV 파일이 다운로드되었습니다')
  }

  // Helper functions
  const resetForm = () => {
    setFormData({
      campaign_id: 1,
      topic: '',
      subtitle: '',
      platform: 'Youtube',
      publish_date: '',
      status: 'draft',
      target_audience: '',
      keywords: '',
      notes: ''
    })
  }

  const openEditModal = (item: ContentSchedule) => {
    setEditingItem(item)
    setFormData({
      campaign_id: 1, // Default
      topic: item['주제'],
      subtitle: item['소제목'],
      platform: item['플랫폼'],
      publish_date: item['발행일'],
      status: item['상태'],
      target_audience: '',
      keywords: '',
      notes: ''
    })
    setShowEditModal(true)
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === schedules.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(schedules.map(s => s.id))
    }
  }

  const toggleSelect = (id: number) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(sid => sid !== id))
    } else {
      setSelectedIds([...selectedIds, id])
    }
  }

  return (
    <AppShell
      title="콘텐츠 스케줄"
      subtitle="SQLite 기반 스케줄 CRUD · 페이지네이션 · 필터"
    >
      <div>

        {/* Toast Notification */}
        {toast && (
          <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg ${
            toast.type === 'success' ? 'bg-green-500' :
            toast.type === 'error' ? 'bg-red-500' :
            'bg-blue-500'
          } text-white font-semibold animate-fade-in`}>
            {toast.message}
          </div>
        )}

        {/* Filters & Actions */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 mb-6">
          {/* Search & Filters Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            {/* Search */}
            <input
              type="text"
              placeholder="🔍 검색 (주제, 소제목, 키워드)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            {/* Platform Filter */}
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 플랫폼</option>
              <option value="Youtube">Youtube</option>
              <option value="Instagram">Instagram</option>
              <option value="TikTok">TikTok</option>
              <option value="Facebook">Facebook</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 상태</option>
              <option value="draft">Draft</option>
              <option value="scheduled">Scheduled</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>

            {/* Items per page */}
            <select
              value={itemsPerPage}
              onChange={(e) => setItemsPerPage(Number(e.target.value))}
              className="px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="5">5개씩</option>
              <option value="10">10개씩</option>
              <option value="20">20개씩</option>
              <option value="50">50개씩</option>
            </select>
          </div>

          {/* Actions Row */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 rounded-lg font-semibold"
            >
              ➕ 새 스케줄
            </button>

            <button
              onClick={exportToCSV}
              disabled={schedules.length === 0}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold disabled:opacity-50"
            >
              📥 CSV 내보내기
            </button>

            {selectedIds.length > 0 && (
              <>
                <button
                  onClick={bulkDelete}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold"
                >
                  🗑️ 선택 삭제 ({selectedIds.length})
                </button>

                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      bulkUpdateStatus(e.target.value)
                      e.target.value = ''
                    }
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
                >
                  <option value="">상태 일괄 변경</option>
                  <option value="draft">Draft</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="published">Published</option>
                  <option value="archived">Archived</option>
                </select>
              </>
            )}

            <button
              onClick={loadSchedules}
              disabled={loading}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg font-semibold disabled:opacity-50"
            >
              🔄 새로고침
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">
              📊 스케줄 목록 ({totalCount}개)
            </h2>
            {loading && (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span className="text-sm">로딩 중...</span>
              </div>
            )}
          </div>

          {schedules.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              스케줄이 없습니다
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedIds.length === schedules.length}
                        onChange={toggleSelectAll}
                        className="w-4 h-4"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">소제목</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">캠페인명</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">플랫폼</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">발행일</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">상태</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">액션</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((item) => (
                    <tr key={item.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(item.id)}
                          onChange={() => toggleSelect(item.id)}
                          className="w-4 h-4"
                        />
                      </td>
                      <td className="px-4 py-3 text-sm">{item.id}</td>
                      <td className="px-4 py-3 text-sm font-semibold">{item['소제목']}</td>
                      <td className="px-4 py-3 text-sm">{item['캠페인명']}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-semibold">
                          {item['플랫폼']}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">{item['발행일']}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          item['상태'] === 'draft' ? 'bg-gray-500/20 text-gray-400' :
                          item['상태'] === 'scheduled' ? 'bg-yellow-500/20 text-yellow-400' :
                          item['상태'] === 'published' ? 'bg-green-500/20 text-green-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {item['상태']}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEditModal(item)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs font-semibold"
                          >
                            ✏️ 수정
                          </button>
                          <button
                            onClick={() => deleteSchedule(item.id)}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs font-semibold"
                          >
                            🗑️ 삭제
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← 이전
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`px-4 py-2 rounded-lg font-semibold ${
                  currentPage === page
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                {page}
              </button>
            ))}

            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              다음 →
            </button>
          </div>
        )}

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 rounded-2xl p-8 max-w-2xl w-full border border-white/20">
              <h2 className="text-2xl font-bold mb-6">➕ 새 스케줄 생성</h2>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">주제 *</label>
                  <input
                    type="text"
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">소제목 *</label>
                  <input
                    type="text"
                    value={formData.subtitle}
                    onChange={(e) => setFormData({ ...formData, subtitle: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">플랫폼 *</label>
                  <select
                    value={formData.platform}
                    onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Youtube">Youtube</option>
                    <option value="Instagram">Instagram</option>
                    <option value="TikTok">TikTok</option>
                    <option value="Facebook">Facebook</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">발행일</label>
                  <input
                    type="date"
                    value={formData.publish_date}
                    onChange={(e) => setFormData({ ...formData, publish_date: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">상태</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="draft">Draft</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="published">Published</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={createSchedule}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 rounded-lg font-semibold disabled:opacity-50"
                >
                  {loading ? '생성 중...' : '생성'}
                </button>
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    resetForm()
                  }}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-semibold"
                >
                  취소
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && editingItem && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 rounded-2xl p-8 max-w-2xl w-full border border-white/20">
              <h2 className="text-2xl font-bold mb-6">✏️ 스케줄 수정</h2>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">주제 *</label>
                  <input
                    type="text"
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">소제목 *</label>
                  <input
                    type="text"
                    value={formData.subtitle}
                    onChange={(e) => setFormData({ ...formData, subtitle: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">플랫폼 *</label>
                  <select
                    value={formData.platform}
                    onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Youtube">Youtube</option>
                    <option value="Instagram">Instagram</option>
                    <option value="TikTok">TikTok</option>
                    <option value="Facebook">Facebook</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">발행일</label>
                  <input
                    type="date"
                    value={formData.publish_date}
                    onChange={(e) => setFormData({ ...formData, publish_date: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">상태</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="draft">Draft</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="published">Published</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={updateSchedule}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg font-semibold disabled:opacity-50"
                >
                  {loading ? '수정 중...' : '수정'}
                </button>
                <button
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingItem(null)
                    resetForm()
                  }}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg font-semibold"
                >
                  취소
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </AppShell>
  )
}
