'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Building2, Plus } from 'lucide-react'
import CampaignCreateModal from './CampaignCreateModal'

interface Client {
  id: number
  name: string
  brand_color?: string
  logo_url?: string
  industry?: string
  contact_email?: string
}

interface Campaign {
  id: number
  name: string
  client_id: number
  status?: 'active' | 'paused' | 'completed'
}

interface ClientsListProps {
  onCampaignSelect?: (campaign: Campaign) => void
}

export default function ClientsList({ onCampaignSelect }: ClientsListProps) {
  const [clients, setClients] = useState<Client[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [showCampaignModal, setShowCampaignModal] = useState(false)
  const [campaignModalClientId, setCampaignModalClientId] = useState<number | null>(null)

  // SQLite에서 클라이언트 및 캠페인 로드
  useEffect(() => {
    loadClients()
  }, [])

  const loadClients = async () => {
    try {
      setLoading(true)
      // API 라우트를 통해 데이터 로드 (서버 컴포넌트에서만 직접 import 가능)
      const res = await fetch('/api/clients')
      if (res.ok) {
        const data = await res.json()
        setClients(data.clients || [])
        setCampaigns(data.campaigns || [])
      } else {
        console.error('Failed to load clients:', await res.text())
      }
    } catch (error) {
      console.error('Failed to load clients:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleExpand = (clientId: number) => {
    const newExpanded = new Set(expanded)
    if (newExpanded.has(clientId)) {
      newExpanded.delete(clientId)
    } else {
      newExpanded.add(clientId)
    }
    setExpanded(newExpanded)
  }

  const getClientCampaigns = (clientId: number) => {
    return campaigns.filter(c => c.client_id === clientId)
  }

  const getCampaignStatusColor = (status?: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'paused': return 'bg-yellow-500'
      case 'completed': return 'bg-gray-500'
      default: return 'bg-blue-500'
    }
  }

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Building2 size={16} />
            클라이언트
          </h3>
        </div>
        <div className="text-sm text-gray-500 text-center py-4">
          로딩 중...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <Building2 size={16} />
          클라이언트
        </h3>
        <button
          onClick={() => {/* TODO: 새 클라이언트 모달 */}}
          className="p-1 hover:bg-gray-700 rounded transition-colors"
          title="새 클라이언트 추가"
        >
          <Plus size={16} />
        </button>
      </div>

      {clients.length === 0 ? (
        <div className="text-sm text-gray-500 text-center py-4">
          클라이언트가 없습니다
        </div>
      ) : (
        clients.map(client => {
          const clientCampaigns = getClientCampaigns(client.id)
          const isExpanded = expanded.has(client.id)

          return (
            <div key={client.id} className="space-y-1">
              <div
                className={`flex items-center gap-2 px-3 py-2 rounded cursor-pointer transition-colors ${
                  selectedClientId === client.id
                    ? 'bg-purple-600 text-white'
                    : 'hover:bg-gray-700 text-gray-300'
                }`}
                onClick={() => {
                  setSelectedClientId(client.id)
                  setSelectedCampaignId(null)
                }}
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleExpand(client.id)
                  }}
                  className="p-0.5 hover:bg-gray-600 rounded"
                >
                  {isExpanded ? (
                    <ChevronDown size={14} />
                  ) : (
                    <ChevronRight size={14} />
                  )}
                </button>

                {client.logo_url ? (
                  <img
                    src={client.logo_url}
                    alt={client.name}
                    className="w-5 h-5 rounded object-cover"
                  />
                ) : (
                  <div
                    className="w-5 h-5 rounded flex items-center justify-center text-xs font-bold"
                    style={{ backgroundColor: client.brand_color || '#6B7280' }}
                  >
                    {client.name[0]}
                  </div>
                )}

                <span className="text-sm flex-1 truncate">{client.name}</span>

                {clientCampaigns.length > 0 && (
                  <span className="text-xs bg-gray-600 px-1.5 py-0.5 rounded">
                    {clientCampaigns.length}
                  </span>
                )}
              </div>

              {/* 캠페인 목록 */}
              {isExpanded && (
                <div className="ml-6 space-y-1 border-l border-gray-700 pl-2">
                  {clientCampaigns.map(campaign => (
                    <div
                      key={campaign.id}
                      onClick={() => {
                        setSelectedClientId(client.id)
                        setSelectedCampaignId(campaign.id)
                        // 부모 컴포넌트에 캠페인 선택 알림
                        if (onCampaignSelect) {
                          onCampaignSelect(campaign)
                        }
                      }}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded cursor-pointer transition-colors text-sm ${
                        selectedCampaignId === campaign.id
                          ? 'bg-purple-500 text-white'
                          : 'hover:bg-gray-700 text-gray-400'
                      }`}
                    >
                      <div
                        className={`w-2 h-2 rounded-full ${getCampaignStatusColor(campaign.status)}`}
                        title={campaign.status || 'active'}
                      ></div>
                      <span className="flex-1 truncate">{campaign.name}</span>
                    </div>
                  ))}

                  {/* 캠페인 추가 버튼 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setCampaignModalClientId(client.id)
                      setShowCampaignModal(true)
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 rounded text-sm text-gray-400 hover:bg-gray-700 hover:text-purple-400 transition-colors w-full"
                  >
                    <Plus size={14} />
                    <span>새 캠페인</span>
                  </button>
                </div>
              )}
            </div>
          )
        })
      )}

      {/* 캠페인 생성 모달 */}
      {showCampaignModal && campaignModalClientId && (
        <CampaignCreateModal
          isOpen={showCampaignModal}
          onClose={() => {
            setShowCampaignModal(false)
            setCampaignModalClientId(null)
          }}
          clientId={campaignModalClientId}
          onSuccess={() => {
            loadClients() // 캠페인 목록 갱신
          }}
        />
      )}
    </div>
  )
}
