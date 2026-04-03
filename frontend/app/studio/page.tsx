"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Save,
  Download,
  Upload,
  Settings,
  Wand2,
  Volume2,
  Type,
  Image as ImageIcon,
  Music,
  X,
  Plus,
  ArrowUp,
  ArrowDown,
  BarChart3,
  Database,
  Folder,
  ChevronRight,
  Zap,
  Share2,
  Clock,
  ArrowRight,
  Layout,
  ChevronDown,
} from "lucide-react";
import ClientsList from "@/components/ClientsList";
import AudioWaveform from "@/components/AudioWaveform";
import BlockList from "@/components/BlockList";
import BlockEffectsEditor from "@/components/BlockEffectsEditor";
import AddBlockButton from "@/components/AddBlockButton";
import {
  ScriptBlock,
  splitScriptIntoBlocks,
  reorderBlocks,
} from "@/lib/blocks/types";
import StudioSidebar from "@/components/studio/StudioSidebar";
import StudioHeader from "@/components/studio/StudioHeader";
import StudioPreview from "@/components/studio/StudioPreview";
import StudioTimeline from "@/components/studio/StudioTimeline";
import StudioInspector from "@/components/studio/StudioInspector";
import {
  addBlock as utilAddBlock,
  deleteBlock as utilDeleteBlock,
  updateBlock as utilUpdateBlock,
  duplicateBlock as utilDuplicateBlock,
  getTotalDuration
} from "@/lib/blocks/utils";
import { Button } from "@/components/ui/Button";
import ABTestManager from "@/components/ABTestManager";
import TemplateBanner from "@/components/studio/TemplateBanner";
import { loadTemplatePreset, generateTemplateBlocks, type TemplatePreset } from "@/lib/template-loader";

interface Campaign {
  id: number;
  name: string;
  client_id: number;
  status?: "active" | "paused" | "completed";
  concept_gender?: string;
  concept_tone?: string;
  concept_style?: string;
  target_duration?: number;
}

// StudioPage 내부 컴포넌트 (useSearchParams 사용)
function StudioPageContent() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(180); // 기본 180초 (3분)
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(
    null,
  );
  const [showSheetsModal, setShowSheetsModal] = useState(false);
  const [showContentCreateForm, setShowContentCreateForm] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"preview" | "script" | "storyboard">("preview");
  const [newContent, setNewContent] = useState({
    title: "",
    platform: "Youtube",
    publish_date: "",
    topic: "",
  });
  const [connectionResult, setConnectionResult] = useState<{
    success: boolean;
    message: string;
    spreadsheet_id?: string;
  } | null>(null);
  const [scheduleItems, setScheduleItems] = useState<any[]>([]);
  const [showSchedule, setShowSchedule] = useState(false);
  const [workflowStep, setWorkflowStep] = useState<string | null>(null);
  const [showDriveSelect, setShowDriveSelect] = useState(false);
  const [clients, setClients] = useState<any[]>([]);
  const [selectedClient, setSelectedClient] = useState<any | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();

  // ✅ URL 파라미터 처리 (Deep Linking)
  useEffect(() => {
    const contentIdParam = searchParams.get("contentId");
    const durationParam = searchParams.get("duration");
    const modeParam = searchParams.get("mode");

    if (contentIdParam && modeParam === "video") {
      const contentId = parseInt(contentIdParam);

      // 상태 초기화
      setCurrentContentId(contentId);
      if (durationParam) {
        setDuration(parseInt(durationParam));
      }

      // 콘텐츠 상세 로드 및 워크플로우 시작
      loadContentAndStartWorkflow(contentId);
    }

    // ✅ Upload 페이지에서 전달된 voice_id / presentation_id 처리
    const voiceIdParam = searchParams.get("voice_id");
    const presentationIdParam = searchParams.get("presentation_id");
    if (voiceIdParam || presentationIdParam) {
      setWorkflowStep("upload_ready");
      if (presentationIdParam) {
        setCurrentContentId(null); // 기존 content 연결 초기화
      }
    }

    // ✅ 템플릿으로 시작 (contentId 없을 때만 적용)
    const templateParam = searchParams.get("template");
    if (templateParam && !contentIdParam) {
      const preset = loadTemplatePreset(templateParam);
      if (preset) {
        setSelectedCampaign({
          id: -1,
          name: preset.name,
          client_id: 0,
          status: "active",
          concept_tone: preset.tone[0] || "",
          target_duration: preset.duration,
        });
        setDuration(preset.duration);
        setBlocks(generateTemplateBlocks(preset));
        setTemplateBannerData(preset);
        setWorkflowStep("template_ready");
      }
    }
  }, [searchParams]);

  const loadContentAndStartWorkflow = async (id: number) => {
    try {
      // 로컬 프록시 API 사용으로 안정성 확보
      const res = await fetch(`/api/content-schedule?content_id=${id}`);
      if (!res.ok) return;

      const data = await res.json();
      if (!data.success || !data.content) {
        console.warn("⚠️ 딥링크 대상 콘텐츠를 찾을 수 없습니다.");
        return;
      }

      const item = data.content;

      // UI 설정
      setShowSheetsModal(false);
      setWorkflowStep("script_generating");

      // 워크플로우 실행을 위한 데이터 매핑
      const mappedItem = {
        id: item.id,
        "캠페인명": item.campaign_name || "기본 캠페인",
        "소제목": item.subtitle || item.title || "제목 없음",
        "주제": item.topic || "",
        "플랫폼": item.platform || "YouTube",
        "발행일": item.publish_date
      };

      // 스크립트 생성 로직 호출
      triggerScriptGeneration(mappedItem);
    } catch (e) {
      console.error("Deep link load failed:", e);
    }
  };


  const triggerScriptGeneration = async (item: any) => {
    // 1단계: 스크립트 생성 시작
    setWorkflowStep("script_generating");

    try {
      const targetDuration = parseInt(searchParams.get("duration") || "180");

      console.log(`🎬 스크립트 생성 시작 (목표: ${targetDuration}초)`);

      // 🔍 1. Writer Agent: 스크립트 생성
      const res = await fetch("/api/writer-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_id: item.id,
          spreadsheet_id: connectionResult?.spreadsheet_id,
          campaign_name: item["캠페인명"],
          topic: item["소제목"] || item["주제"],
          platform: item["플랫폼"] || "YouTube",
          target_duration: targetDuration,
          regenerate: true, // 강제 재생성
        }),
      });

      const data = await res.json();
      setScriptCached(data.cached || false);
      setScriptLoadedAt(data.metadata?.loaded_at || data.metadata?.generated_at || null);

      if (data.success) {
        setGeneratedScript(data.script || data.body || "");
        console.log("✅ 스크립트 생성 완료, 스토리보드 분할 시작...");

        // 🔍 2. Storyboard API: 블록 분할
        try {
          const storyboardRes = await fetch(
            `/api/storyboard/campaigns/${selectedCampaign?.id || 1}/content/${item.id}/generate`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                script: data.script,
                campaign_concept: {
                  gender: selectedCampaign?.concept_gender || "neutral",
                  tone: selectedCampaign?.concept_tone || "professional",
                  style: selectedCampaign?.concept_style || "modern",
                  platform: item["플랫폼"] || "YouTube",
                },
                target_duration: targetDuration,
              }),
            },
          );

          const storyboardData = await storyboardRes.json();

          if (storyboardData.success && storyboardData.storyboard_blocks?.length > 0) {
            // AI가 생성한 동적 블록을 ScriptBlock으로 변환
            const colors = [
              "bg-red-500", "bg-blue-500", "bg-green-500",
              "bg-yellow-500", "bg-purple-500", "bg-pink-500"
            ];

            const newBlocks = storyboardData.storyboard_blocks.map((block: any, idx: number) => ({
              id: `block-${Date.now()}-${idx}`,
              type: (block.block_type || "body").toLowerCase(),
              content: block.content, // 여기가 중요: 분할된 스크립트 내용
              duration: Math.round(block.end_time - block.start_time),
              effects: {},
              media: {},
              timing: {
                start: block.start_time,
                end: block.end_time
              },
              order: idx,
              color: colors[idx % colors.length]
            }));

            setBlocks(newBlocks);
            console.log(`✅ 스토리보드 분할 완료: ${newBlocks.length}개 블록`);
          } else {
            console.warn("⚠️ 스토리보드 API 응답 없음, 기본 분할 사용");
            // Fallback: 단순 3등분
            const partDuration = Math.floor(targetDuration / 3);
            setBlocks([
              { id: "hook-fb", type: "hook", content: data.hook || data.script.substring(0, 50), duration: partDuration, timing: { start: 0, end: partDuration }, order: 0, effects: {}, media: {} },
              { id: "body-fb", type: "body", content: data.script.substring(50), duration: partDuration, timing: { start: partDuration, end: partDuration * 2 }, order: 1, effects: {}, media: {} },
              { id: "cta-fb", type: "cta", content: data.cta || "구독 좋아요", duration: partDuration, timing: { start: partDuration * 2, end: targetDuration }, order: 2, effects: {}, media: {} }
            ]);
          }

        } catch (storyErr) {
          console.error("스토리보드 생성 실패:", storyErr);
        }

        setWorkflowStep("script_ready");
        setActiveTab("script");
      }
    } catch (err) {
      console.error("Workflow trigger failed:", err);
    }
  };

  // ✅ 블록 시스템으로 전환 (VREW 스타일 동적 블록)
  const [blocks, setBlocks] = useState<ScriptBlock[]>([
    {
      id: "hook-0",
      type: "hook",
      content: "여러분, 2026년 AI 트렌드를 알아볼까요?",
      duration: 5,
      effects: { fadeIn: true },
      media: {},
      timing: { start: 0, end: 5 },
      order: 0,
    },
    {
      id: "body-0",
      type: "body",
      content: "첫 번째로 생성형 AI가 급격히 발전하고 있습니다...",
      duration: 8,
      effects: {},
      media: {},
      timing: { start: 5, end: 13 },
      order: 1,
    },
    {
      id: "cta-0",
      type: "cta",
      content: "좋아요와 구독 부탁드립니다!",
      duration: 4,
      effects: { highlight: true, fadeOut: true },
      media: {},
      timing: { start: 13, end: 17 },
      order: 2,
    },
  ]);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);

  // ✅ 추가: 현재 작업 중인 콘텐츠 ID 및 결과물 URL 저장
  const [currentContentId, setCurrentContentId] = useState<number | null>(null);
  const [generatedScript, setGeneratedScript] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [scriptCached, setScriptCached] = useState<boolean>(false);
  const [scriptLoadedAt, setScriptLoadedAt] = useState<string | null>(null);
  const [renderProgress, setRenderProgress] = useState<number>(0);
  const [renderStatus, setRenderStatus] = useState<string>("");
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // 템플릿 배너 상태
  const [templateBannerData, setTemplateBannerData] = useState<TemplatePreset | null>(null);

  // A/B 테스트 모달 상태
  // A/B 테스트 모달 상태
  const [showABTestModal, setShowABTestModal] = useState(false);

  // ✅ 오디오 진행률 상태 추가
  const [audioProgress, setAudioProgress] = useState(0);
  const [audioStatusMessage, setAudioStatusMessage] = useState("");

  // 모달이 열릴 때 자동으로 스케줄 로드
  useEffect(() => {
    if (showSheetsModal) {
      setLoading(true);
      loadSchedule("auto");
    }
  }, [showSheetsModal]);

  // 구글 시트 연결
  const connectSheet = async () => {
    if (!sheetUrl.trim()) {
      alert("구글 시트 URL을 입력해주세요");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/sheets-connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spreadsheet_url: sheetUrl }),
      });

      const data = await res.json();
      setConnectionResult(data);

      if (data.success && data.spreadsheet_id) {
        // 연결 성공 시 스케줄 자동 로드
        loadSchedule(data.spreadsheet_id);
      }
    } catch (err) {
      console.error("연결 실패:", err);
      setConnectionResult({
        success: false,
        message: "연결 중 오류가 발생했습니다",
      });
    } finally {
      setLoading(false);
    }
  };

  // ✅ 블록 CRUD 함수들
  const addBlock = () => {
    const newOrder = blocks.length;
    const lastBlock = blocks[blocks.length - 1];
    const startTime = lastBlock ? lastBlock.timing.end : 0;

    const newBlock: ScriptBlock = {
      id: `block-${Date.now()}`,
      type: "body",
      content: "새 블록 내용을 입력하세요...",
      duration: 5,
      effects: {},
      media: {},
      timing: { start: startTime, end: startTime + 5 },
      order: newOrder,
    };

    setBlocks([...blocks, newBlock]);
    setSelectedBlockId(newBlock.id);
  };

  const updateBlock = (updatedBlock: ScriptBlock) => {
    setBlocks((prev) => {
      const updated = prev.map((b) =>
        b.id === updatedBlock.id ? updatedBlock : b,
      );
      return reorderBlocks(updated);
    });
  };

  // ✅ 스크립트 자동 저장 (blocks 변경 시)
  useEffect(() => {
    if (!currentContentId || blocks.length === 0) return;

    const saveScript = async () => {
      try {
        const res = await fetch('/api/content-script', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content_id: currentContentId, blocks }),
        });

        if (res.ok) {
          console.log('💾 스크립트 자동 저장 완료');
        }
      } catch (error) {
        console.error('스크립트 저장 실패:', error);
      }
    };

    // Debounce: 500ms 후 저장
    const timeoutId = setTimeout(saveScript, 500);
    return () => clearTimeout(timeoutId);
  }, [blocks, currentContentId]);

  // ✅ 스크립트 자동 로드 (currentContentId 변경 시)
  useEffect(() => {
    if (!currentContentId) return;

    const loadScript = async () => {
      try {
        const res = await fetch(`/api/content-script?content_id=${currentContentId}`);
        const data = await res.json();

        if (data.success && data.script_data && Array.isArray(data.script_data) && data.script_data.length > 0) {
          setBlocks(data.script_data);
          console.log(`📜 저장된 스크립트 로드 완료 (${data.script_data.length}개 블록)`);
        } else {
          console.log('📜 저장된 스크립트 없음 - 새로 생성된 블록 유지');
        }
      } catch (error) {
        console.error('스크립트 로드 실패:', error);
      }
    };

    // 약간의 딜레이를 주어 applyScheduleToTimeline의 setBlocks() 이후에 실행
    setTimeout(loadScript, 100);
  }, [currentContentId]);

  const deleteBlock = (blockId: string) => {
    setBlocks((prev) => {
      const filtered = prev.filter((b) => b.id !== blockId);
      return reorderBlocks(filtered);
    });
    if (selectedBlockId === blockId) {
      setSelectedBlockId(null);
    }
  };

  const duplicateBlock = (blockId: string) => {
    const block = blocks.find((b) => b.id === blockId);
    if (!block) return;

    const newBlock: ScriptBlock = {
      ...block,
      id: `block-${Date.now()}`,
      order: block.order + 1,
    };

    const newBlocks = [
      ...blocks.slice(0, block.order + 1),
      newBlock,
      ...blocks.slice(block.order + 1),
    ];

    setBlocks(reorderBlocks(newBlocks));
  };

  const moveBlockUp = (blockId: string) => {
    const index = blocks.findIndex((b) => b.id === blockId);
    if (index <= 0) return;

    const newBlocks = [...blocks];
    const temp = newBlocks[index - 1];
    newBlocks[index - 1] = newBlocks[index];
    newBlocks[index] = temp;

    setBlocks(reorderBlocks(newBlocks));
  };

  const moveBlockDown = (blockId: string) => {
    const index = blocks.findIndex((b) => b.id === blockId);
    if (index < 0 || index >= blocks.length - 1) return;

    const newBlocks = [...blocks];
    const temp = newBlocks[index + 1];
    newBlocks[index + 1] = newBlocks[index];
    newBlocks[index] = temp;

    setBlocks(reorderBlocks(newBlocks));
  };

  const splitBlock = (blockId: string) => {
    const block = blocks.find((b) => b.id === blockId);
    if (!block) return;

    // 문장 단위로 분할 (마침표, 물음표, 느낌표 기준)
    const sentences = block.content.split(/([.!?]\s+)/).filter(s => s.trim().length > 0);

    if (sentences.length <= 1) {
      alert('문장이 너무 짧아서 분할할 수 없습니다.');
      return;
    }

    // 전체 글자 수
    const totalLength = block.content.length;
    const targetMidPoint = totalLength / 2;

    // 중간 지점에 가장 가까운 문장 경계 찾기
    let currentLength = 0;
    let splitIndex = 0;
    let minDistance = Infinity;

    for (let i = 0; i < sentences.length; i++) {
      currentLength += sentences[i].length;
      const distance = Math.abs(currentLength - targetMidPoint);

      if (distance < minDistance) {
        minDistance = distance;
        splitIndex = i + 1;
      }
    }

    // 첫 번째와 두 번째 그룹으로 분할
    const firstSentences = sentences.slice(0, splitIndex).join('');
    const secondSentences = sentences.slice(splitIndex).join('');

    if (!firstSentences.trim() || !secondSentences.trim()) {
      alert('분할할 수 없는 위치입니다.');
      return;
    }

    // Duration을 문장 길이 비율로 계산
    const firstRatio = firstSentences.length / totalLength;
    const firstDuration = Math.floor(block.duration * firstRatio);
    const secondDuration = block.duration - firstDuration;

    // 첫 번째 블록
    const firstBlock: ScriptBlock = {
      ...block,
      duration: firstDuration,
      content: firstSentences.trim(),
      timing: {
        start: block.timing.start,
        end: block.timing.start + firstDuration,
      },
    };

    // 두 번째 블록
    const secondBlock: ScriptBlock = {
      ...block,
      id: `block-${Date.now()}`,
      order: block.order + 1,
      duration: secondDuration,
      content: secondSentences.trim(),
      timing: {
        start: block.timing.start + firstDuration,
        end: block.timing.end,
      },
    };

    // 배열에서 원본 블록을 첫 번째, 두 번째 블록으로 교체
    const newBlocks = [
      ...blocks.slice(0, block.order),
      firstBlock,
      secondBlock,
      ...blocks.slice(block.order + 1),
    ];

    console.log(`✂️ 블록 분할: ${block.type} (${block.duration}초) → ${firstDuration}초 + ${secondDuration}초`);
    console.log(`   첫 번째: "${firstSentences.substring(0, 30)}..."`);
    console.log(`   두 번째: "${secondSentences.substring(0, 30)}..."`);
    setBlocks(reorderBlocks(newBlocks));
  };

  const autoSplitBlock = async (blockId: string) => {
    const block = blocks.find((b) => b.id === blockId);
    if (!block) return;

    if (block.content.length < 50) {
      alert('블록이 너무 짧아서 자동 분할이 불필요합니다.');
      return;
    }

    console.log(`🤖 AI 맥락 기반 자동 분할 시작: ${block.type} (${block.duration}초)`);

    try {
      // Storyboard API 호출 (맥락 분석 기반 분할)
      const response = await fetch(
        `/api/storyboard/campaigns/1/content/1/generate?async_mode=false`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            script: block.content,
            campaign_concept: {
              gender: 'female',
              tone: 'professional',
              style: 'modern',
              platform: 'YouTube'
            },
            target_duration: block.duration
          })
        }
      );

      if (!response.ok) {
        throw new Error('AI 분할 실패');
      }

      const data = await response.json();

      if (!data.success || !data.storyboard_blocks || data.storyboard_blocks.length === 0) {
        alert('AI가 의미 있는 분할 지점을 찾지 못했습니다.');
        return;
      }

      console.log(`✅ AI가 ${data.storyboard_blocks.length}개 블록으로 분할 완료`);

      // Storyboard 블록을 ScriptBlock으로 변환
      const splitBlocks: ScriptBlock[] = data.storyboard_blocks.map((sb: any, idx: number) => ({
        id: idx === 0 ? block.id : `block-${Date.now()}-${idx}`,
        type: sb.block_type || block.type,
        content: sb.content,
        duration: Math.round(sb.end_time - sb.start_time),
        effects: {
          fadeIn: sb.transition_in === 'fade',
          fadeOut: sb.transition_out === 'fade',
          zoomIn: sb.transition_in === 'zoom',
          zoomOut: sb.transition_out === 'zoom',
          slide: sb.transition_in?.includes('slide') ? sb.transition_in : undefined,
          highlight: sb.visual_emphasis === 'highlight'
        },
        media: {
          backgroundUrl: sb.background_url,
          backgroundType: sb.background_type
        },
        timing: {
          start: block.timing.start + sb.start_time,
          end: block.timing.start + sb.end_time
        },
        order: block.order + idx
      }));

      // 원본 블록을 AI 분할 블록들로 교체
      const newBlocks = [
        ...blocks.slice(0, block.order),
        ...splitBlocks,
        ...blocks.slice(block.order + 1),
      ];

      setBlocks(reorderBlocks(newBlocks));
      alert(`AI가 맥락을 분석하여 ${splitBlocks.length}개 블록으로 분할했습니다!`);

    } catch (error) {
      console.error('AI 자동 분할 실패:', error);
      alert('AI 분할 중 오류가 발생했습니다. 백엔드가 실행 중인지 확인해주세요.');
    }
  };

  const mergeWithNextBlock = (blockId: string) => {
    const blockIndex = blocks.findIndex((b) => b.id === blockId);
    if (blockIndex === -1 || blockIndex >= blocks.length - 1) {
      alert('다음 블록이 없어서 합칠 수 없습니다.');
      return;
    }

    const currentBlock = blocks[blockIndex];
    const nextBlock = blocks[blockIndex + 1];

    // 두 블록 합치기
    const mergedBlock: ScriptBlock = {
      ...currentBlock,
      duration: currentBlock.duration + nextBlock.duration,
      content: `${currentBlock.content} ${nextBlock.content}`.trim(),
      timing: {
        start: currentBlock.timing.start,
        end: nextBlock.timing.end,
      },
    };

    // 다음 블록 제거하고 현재 블록을 합쳐진 블록으로 교체
    const newBlocks = [
      ...blocks.slice(0, blockIndex),
      mergedBlock,
      ...blocks.slice(blockIndex + 2),
    ];

    console.log(`🔗 블록 합치기: ${currentBlock.duration}초 + ${nextBlock.duration}초 → ${mergedBlock.duration}초`);
    setBlocks(reorderBlocks(newBlocks));
  };

  const reorderBlocksByDragDrop = (reorderedBlocks: ScriptBlock[]) => {
    // 드래그 앤 드롭으로 순서 변경 시, 타이밍 자동 재계산
    setBlocks(reorderBlocks(reorderedBlocks));
  };

  // 스케줄 불러오기
  const loadSchedule = async (spreadsheetId: string) => {
    try {
      const res = await fetch(
        `/api/content-schedule?spreadsheet_id=${spreadsheetId}`,
      );
      const data = await res.json();

      if (data.success) {
        // DB 데이터를 컴포넌트에서 사용하는 형식으로 매핑
        const rawItems = data.contents || data.schedule || [];
        const mappedItems = rawItems.map((item: any) => ({
          ...item,
          // DB 필드가 있으면 사용, 없으면 기존 키 사용 (호환성)
          "캠페인명": item.campaign_name || item["캠페인명"] || "미지정 캠페인",
          "소제목": item.subtitle || item["소제목"] || "",
          "주제": item.topic || item["주제"] || "",
          "플랫폼": item.platform || item["플랫폼"] || "YouTube",
          "발행일": item.publish_date || item["발행일"] || "",
          "상태": item.status || item["상태"] || "draft"
        }));

        // 선택된 캠페인에 속한 콘텐츠만 필터링
        let filteredSchedule = mappedItems;

        if (selectedCampaign) {
          filteredSchedule = mappedItems.filter(
            (item: any) => item["캠페인명"] === selectedCampaign.name,
          );
          console.log(
            `📋 "${selectedCampaign.name}" 캠페인 콘텐츠: ${filteredSchedule.length}개`,
          );
        }

        setScheduleItems(filteredSchedule);
        console.log(
          "✅ 로드된 스케줄:",
          filteredSchedule.length,
          "개",
        );
      } else {
        console.error("❌ 스케줄 로드 실패:", data.message || data.error);
      }
    } catch (err) {
      console.error("❌ 스케줄 로드 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  // 스케줄 항목 선택하여 타임라인에 적용 (라우팅 변경)
  const applyScheduleToTimeline = async (item: any) => {
    // 선택 화면으로 이동
    router.push(`/studio/content/${item.id}/edit`);
  };

  /* 기존 로직 백업 (Deep Linking에서 사용됨) */
  const _unused_applyScheduleToTimeline = async (item: any) => {
    setShowSheetsModal(false);

    // ✅ 콘텐츠 ID 저장 (워크플로우 전체에서 사용)
    setCurrentContentId(item.id);

    // 1단계: 스크립트 생성 시작
    setWorkflowStep("script_generating");

    try {
      const targetDuration = selectedCampaign?.target_duration || 180;

      // 🔍 먼저 기존 스크립트가 있는지 확인
      console.log(`🔍 콘텐츠 ID ${item.id}의 저장된 스크립트 확인 중...`);

      const res = await fetch("/api/writer-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_id: item.id, // SQLite ID 전달
          spreadsheet_id: connectionResult?.spreadsheet_id,
          campaign_name: item["캠페인명"],
          topic: item["소제목"] || item["주제"],
          platform: item["플랫폼"] || "YouTube",
          target_duration: targetDuration,
          regenerate: false, // 기존 스크립트 우선 사용
        }),
      });

      const data = await res.json();

      // 📦 캐시된 스크립트인지 확인하고 상태 저장
      setScriptCached(data.cached || false);
      setScriptLoadedAt(
        data.metadata?.loaded_at || data.metadata?.generated_at || null,
      );

      if (data.cached) {
        console.log("✅ 저장된 스크립트를 불러왔습니다 (DB에서 로드)");
      } else {
        console.log("✨ 새로운 스크립트를 생성했습니다 (Anthropic API 호출)");
      }

      if (data.success) {
        console.log(
          "✅ Writer 스크립트 생성 완료, 이제 Director Agent로 콘티 블록 분할",
        );

        // 캠페인 duration 기준
        const targetDuration = selectedCampaign?.target_duration || duration;

        // Storyboard API 호출 - AI가 동적으로 블록 분할
        try {
          const storyboardRes = await fetch(
            `/api/storyboard/campaigns/${selectedCampaign?.id}/content/${item.id}/generate`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                script: data.script || "",
                campaign_concept: {
                  gender: selectedCampaign?.concept_gender || "neutral",
                  tone: selectedCampaign?.concept_tone || "professional",
                  style: selectedCampaign?.concept_style || "modern",
                  platform: item["플랫폼"] || "YouTube",
                },
                target_duration: targetDuration,
              }),
            },
          );

          const storyboardData = await storyboardRes.json();

          if (
            storyboardData.success &&
            storyboardData.storyboard_blocks?.length > 0
          ) {
            // AI가 생성한 동적 블록을 섹션으로 변환
            const colors = [
              "bg-red-500",
              "bg-blue-500",
              "bg-green-500",
              "bg-yellow-500",
              "bg-purple-500",
              "bg-pink-500",
              "bg-indigo-500",
            ];

            const dynamicSections = storyboardData.storyboard_blocks.map(
              (block: any, index: number) => ({
                id: block.order + 1,
                type: block.emotion || `블록${block.order + 1}`,
                duration: Math.round(block.end_time - block.start_time),
                color: colors[index % colors.length],
                script: block.script,
              }),
            );

            const newBlocks = dynamicSections.map(
              (section: any, idx: number) => ({
                id: `section-${idx}`,
                type: section.type.toLowerCase(),
                content: section.script,
                duration: section.duration,
                effects: {},
                media: {},
                timing: {
                  start: dynamicSections
                    .slice(0, idx)
                    .reduce((sum: number, s: any) => sum + s.duration, 0),
                  end: dynamicSections
                    .slice(0, idx + 1)
                    .reduce((sum: number, s: any) => sum + s.duration, 0),
                },
                order: idx,
              }),
            );
            setBlocks(newBlocks);
            console.log(`✅ AI 콘티 블록 ${newBlocks.length}개 생성 완료`);
          } else {
            console.warn("⚠️ Storyboard 생성 실패, 기본 3블록 사용");

            // Fallback: 기본 3블록
            const hookDuration = Math.round(targetDuration * 0.15);
            const bodyDuration = Math.round(targetDuration * 0.7);
            const ctaDuration = Math.round(targetDuration * 0.15);
            setBlocks([
              {
                id: "hook-fallback",
                type: "hook",
                content: data.hook || "훅 스크립트가 생성됩니다...",
                duration: hookDuration,
                effects: { fadeIn: true },
                media: {},
                timing: { start: 0, end: hookDuration },
                order: 0,
              },
              {
                id: "body-fallback",
                type: "body",
                content: data.script || "본문 스크립트가 생성됩니다...",
                duration: bodyDuration,
                effects: {},
                media: {},
                timing: {
                  start: hookDuration,
                  end: hookDuration + bodyDuration,
                },
                order: 1,
              },
              {
                id: "cta-fallback",
                type: "cta",
                content: data.cta || "CTA 스크립트가 생성됩니다...",
                duration: ctaDuration,
                effects: { highlight: true, fadeOut: true },
                media: {},
                timing: {
                  start: hookDuration + bodyDuration,
                  end: targetDuration,
                },
                order: 2,
              },
            ]);
          }
        } catch (storyboardErr) {
          console.error("❌ Storyboard API 오류:", storyboardErr);

          // Fallback: 기본 3블록
          const hookDuration = Math.round(targetDuration * 0.15);
          const bodyDuration = Math.round(targetDuration * 0.7);
          const ctaDuration = Math.round(targetDuration * 0.15);
          setBlocks([
            {
              id: "hook-error",
              type: "hook",
              content: data.hook || "훅 스크립트가 생성됩니다...",
              duration: hookDuration,
              effects: { fadeIn: true },
              media: {},
              timing: { start: 0, end: hookDuration },
              order: 0,
            },
            {
              id: "body-error",
              type: "body",
              content: data.script || "본문 스크립트가 생성됩니다...",
              duration: bodyDuration,
              effects: {},
              media: {},
              timing: { start: hookDuration, end: hookDuration + bodyDuration },
              order: 1,
            },
            {
              id: "cta-error",
              type: "cta",
              content: data.cta || "CTA 스크립트가 생성됩니다...",
              duration: ctaDuration,
              effects: { highlight: true, fadeOut: true },
              media: {},
              timing: {
                start: hookDuration + bodyDuration,
                end: targetDuration,
              },
              order: 2,
            },
          ]);
        }

        console.log(`✅ AI 스크립트 적용 완료 - ${targetDuration}초 기준`);

        // ✅ 생성된 스크립트를 state에 저장 (이미 DB에 저장됨)
        setGeneratedScript(data.script || data.body || "");

        setWorkflowStep("script_ready");
        setActiveTab("script"); // 스크립트 탭으로 자동 전환
      } else {
        alert(`스크립트 생성 실패: ${data.error || "알 수 없는 오류"}`);
        setWorkflowStep(null);
      }
    } catch (err) {
      console.error("스크립트 생성 실패:", err);
      alert("스크립트 생성 중 오류가 발생했습니다");
      setWorkflowStep(null);
    }
  };

  // 스크립트 재생성 함수
  const regenerateScript = async () => {
    if (!currentContentId || !selectedCampaign) {
      alert("콘텐츠 정보가 없습니다");
      return;
    }

    setWorkflowStep("script_generating");
    setScriptCached(false);

    try {
      const targetDuration = selectedCampaign.target_duration || 180;

      // 현재 선택된 콘텐츠 정보 가져오기
      const currentScheduleItem = scheduleItems.find(
        (item) => item.id === currentContentId,
      );

      if (!currentScheduleItem) {
        alert("현재 콘텐츠를 찾을 수 없습니다");
        setWorkflowStep("script_ready");
        return;
      }

      const res = await fetch("/api/writer-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_id: currentContentId,
          spreadsheet_id: connectionResult?.spreadsheet_id,
          campaign_name: currentScheduleItem["캠페인명"],
          topic: currentScheduleItem["소제목"] || currentScheduleItem["주제"],
          platform: currentScheduleItem["플랫폼"] || "YouTube",
          target_duration: targetDuration,
          regenerate: true, // 강제 재생성
        }),
      });

      const data = await res.json();

      if (data.success) {
        console.log("✨ 스크립트를 새로 생성했습니다");
        setScriptCached(false);
        setScriptLoadedAt(data.metadata?.generated_at || null);

        // 블록 업데이트
        if (data.blocks && data.blocks.length > 0) {
          const newBlocks = data.blocks.map((block: any, index: number) => {
            const prevDuration = data.blocks
              .slice(0, index)
              .reduce((sum: number, b: any) => sum + (b.duration || 0), 0);
            const currDuration = block.duration || 0;
            return {
              id: `block-${index}`,
              type: (block.type || `block${index + 1}`).toLowerCase(),
              content: block.content || "",
              duration: currDuration,
              effects: {},
              media: {},
              timing: { start: prevDuration, end: prevDuration + currDuration },
              order: index,
            };
          });
          setBlocks(newBlocks);
        }

        setWorkflowStep("script_ready");
      } else {
        alert("스크립트 재생성 실패: " + data.error);
        setWorkflowStep("script_ready");
      }
    } catch (error) {
      console.error("재생성 오류:", error);
      alert("스크립트 재생성 중 오류가 발생했습니다");
      setWorkflowStep("script_ready");
    }
  };

  // 오디오 생성 시작
  const generateAudio = async () => {
    setWorkflowStep("audio_generating");

    try {
      // 전체 스크립트 결합 (모든 블록)
      const fullScript = blocks.map((b) => b.content).join("\n\n");

      if (!fullScript.trim()) {
        alert("스크립트가 비어있습니다");
        setWorkflowStep("script_ready");
        return;
      }

      // Audio API 호출 (Celery 비동기 처리)
      const res = await fetch("/api/audio/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: fullScript,
          voice_id:
            selectedCampaign?.concept_gender === "female" ? "rachel" : "josh",
          language: "ko",
          accuracy_threshold: 0.95,
          max_attempts: 5,
        }),
      });

      const data = await res.json();

      if (data.task_id) {
        console.log(`✅ 오디오 생성 작업 시작: ${data.task_id}`);
        setAudioProgress(0);
        setAudioStatusMessage("작업 초기화 중...");

        // 상태 폴링 (1초마다 확인 - 더 빠른 피드백)
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(
              `/api/audio/status/${data.task_id}`,
            );
            const statusData = await statusRes.json();

            // 진행률 업데이트 (Backend가 progress를 반환한다고 가정)
            if (statusData.info && statusData.info.progress !== undefined) {
              setAudioProgress(Math.round(statusData.info.progress * 100));
            } else if (statusData.progress !== undefined) {
              setAudioProgress(Math.round(statusData.progress * 100));
            }

            // 메시지 업데이트
            if (statusData.info && statusData.info.message) {
              setAudioStatusMessage(statusData.info.message);
            } else if (statusData.message) {
              setAudioStatusMessage(statusData.message);
            }

            console.log(`🔄 오디오 생성 상태: ${statusData.status} (${audioProgress}%)`);

            if (statusData.status === "SUCCESS" && statusData.result) {
              clearInterval(pollInterval);
              setAudioProgress(100);
              setAudioStatusMessage("생성 완료!");

              // task_id를 사용한 오디오 다운로드 URL
              const audioUrl = `/api/audio/download/${data.task_id}`;
              setAudioUrl(audioUrl);

              console.log(`✅ 오디오 생성 완료: ${statusData.result.audio_path}`);
              setWorkflowStep("audio_ready");
            } else if (statusData.status === "FAILURE") {
              clearInterval(pollInterval);
              alert(
                `오디오 생성 실패: ${statusData.error || "알 수 없는 오류"}`,
              );
              setWorkflowStep("script_ready");
            }
          } catch (pollErr) {
            console.error("상태 확인 실패:", pollErr);
          }
        }, 1000);
      } else {
        alert("오디오 생성 요청 실패");
        setWorkflowStep("script_ready");
      }
    } catch (err) {
      console.error("오디오 생성 실패:", err);
      alert("오디오 생성 중 오류가 발생했습니다");
      setWorkflowStep("script_ready");
    }
  };

  // 영상 렌더링 시작
  const renderVideo = async () => {
    if (!currentContentId || !audioUrl) {
      alert("콘텐츠 ID 또는 오디오가 없습니다");
      return;
    }

    setWorkflowStep("video_rendering");
    setRenderProgress(0);
    setRenderStatus("영상 생성 작업 시작 중...");

    try {
      // 전체 스크립트 결합
      const fullScript = blocks.map((b) => b.content).join("\n\n");

      // Director Agent API 호출 (비동기 작업)
      const res = await fetch(
        "/api/director/generate-video",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: `content_${currentContentId}`,
            script: fullScript,
            audio_path: audioUrl,
            gender: selectedCampaign?.concept_gender || "female",
            character_style: selectedCampaign?.concept_style || "professional",
            async_mode: true,
          }),
        },
      );

      const data = await res.json();

      if (data.success && data.task_id) {
        console.log(`✅ 영상 생성 작업 시작: ${data.task_id}`);
        setCurrentTaskId(data.task_id);
        setRenderProgress(10);
        setRenderStatus("작업 큐 대기 중...");

        // Celery task 상태 폴링 (3초마다 확인 - 진행률 실시간 표시)
        let pollAttempts = 0;
        const maxAttempts = 1200; // 3600초 = 1시간 최대 대기

        const pollInterval = setInterval(async () => {
          pollAttempts++;
          try {
            // 진행률 API 호출 (Backend director API의 task-status 엔드포인트)
            const statusRes = await fetch(
              `/api/director/task-status/${data.task_id}`,
            );
            const statusData = await statusRes.json();

            console.log(
              `🔄 영상 생성 상태: ${statusData.status} (${statusData.progress?.toFixed(1) || 'N/A'}%)`,
            );

            // UNKNOWN 상태 처리 (Celery 연결 실패)
            if (statusData.status === "UNKNOWN") {
              clearInterval(pollInterval);
              setRenderProgress(0);
              setRenderStatus(
                statusData.error || "영상 생성 실패: Celery 워커 연결 오류"
              );
              // setIsRendering(false); // Removed undefined state setter
              alert(
                `영상 생성 실패\n\n${statusData.message || "Celery 워커가 실행되지 않았거나 연결에 실패했습니다."}\n\n오디오 생성까지만 완료되었습니다.`
              );
              return;
            }

            // 진행률 업데이트
            if (statusData.progress !== undefined) {
              const progressPercent = Math.round(statusData.progress * 100);
              setRenderProgress(progressPercent);
            }

            // 메시지 업데이트
            if (statusData.message) {
              setRenderStatus(statusData.message);
            }

            // 완료 처리
            if (statusData.status === "SUCCESS") {
              clearInterval(pollInterval);
              setRenderProgress(100);
              setRenderStatus("영상 생성 완료!");

              // 결과 데이터에서 영상 경로 추출
              if (statusData.result?.final_video_path) {
                const videoPath = statusData.result.final_video_path;
                const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
                setVideoUrl(`${backendUrl}${videoPath}`);
                console.log(`✅ 영상 생성 완료: ${videoPath}`);
              }

              setTimeout(() => {
                setWorkflowStep("video_ready");
              }, 1500);
            }
            // 실패 처리
            else if (statusData.status === "FAILURE") {
              clearInterval(pollInterval);
              setRenderProgress(0);
              setRenderStatus(
                `영상 생성 실패: ${statusData.error || "알 수 없는 오류"}`,
              );
              alert(`영상 생성 실패: ${statusData.error || "알 수 없는 오류"}`);
              setTimeout(() => {
                setWorkflowStep("audio_ready");
              }, 2000);
            }
          } catch (pollErr) {
            console.error("상태 확인 실패:", pollErr);
            // 네트워크 오류는 무시하고 재시도
          }

          // 타임아웃 처리
          if (pollAttempts >= maxAttempts) {
            clearInterval(pollInterval);
            setRenderStatus("작업 시간 초과");
            alert("영상 생성 작업이 시간을 초과했습니다");
            setWorkflowStep("audio_ready");
          }
        }, 3000); // 3초마다 확인
      } else {
        alert("영상 생성 요청 실패");
        setWorkflowStep("audio_ready");
      }
    } catch (err) {
      console.error("영상 생성 실패:", err);
      alert("영상 생성 중 오류가 발생했습니다");
      setWorkflowStep("audio_ready");
    }
  };

  // 새 콘텐츠 저장
  const handleCreateContent = async () => {
    if (!selectedCampaign || !newContent.title.trim()) {
      alert("소제목을 입력해주세요");
      return;
    }

    try {
      const res = await fetch("/api/content-schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          campaign_id: selectedCampaign.id,
          subtitle: newContent.title,
          topic: newContent.topic || selectedCampaign.name,
          platform: newContent.platform,
          publish_date:
            newContent.publish_date || new Date().toISOString().split("T")[0],
          status: "draft",
        }),
      });

      const data = await res.json();

      if (data.success) {
        console.log("✅ 콘텐츠 생성 성공:", data);

        // 새로 추가된 콘텐츠를 목록에 반영
        const newContentItem = {
          id: data.content_id,
          소제목: newContent.title,
          캠페인명: selectedCampaign.name,
          플랫폼: newContent.platform,
          발행일:
            newContent.publish_date || new Date().toISOString().split("T")[0],
          주제: newContent.topic || selectedCampaign.name,
          상태: "draft",
        };

        setScheduleItems([newContentItem, ...scheduleItems]);
        setShowContentCreateForm(false);
        setNewContent({
          title: "",
          platform: "Youtube",
          publish_date: "",
          topic: "",
        });

        alert("콘텐츠가 추가되었습니다!");
      } else {
        alert(`콘텐츠 생성 실패: ${data.error}`);
      }
    } catch (err) {
      console.error("콘텐츠 생성 실패:", err);
      alert("콘텐츠 생성 실패");
    }
  };

  // 캠페인 선택 핸들러
  const handleCampaignSelect = async (campaign: Campaign) => {
    console.log("🎯 캠페인 선택됨:", campaign);

    setSelectedCampaign(campaign);

    // 캠페인의 콘텐츠 목록 로드
    try {
      const res = await fetch(`/api/content-schedule?campaign_id=${campaign.id}`);
      const data = await res.json();

      if (data.success && Array.isArray(data.contents)) {
        const formattedContents = data.contents.map((item: any) => ({
          id: item.id,
          소제목: item.subtitle,
          캠페인명: campaign.name,
          플랫폼: item.platform,
          발행일: item.publish_date,
          주제: item.topic,
          상태: item.status
        }));
        setScheduleItems(formattedContents);
        console.log(`📋 콘텐츠 ${formattedContents.length}개 로드됨`);
      } else {
        setScheduleItems([]);
        console.log("📋 콘텐츠 없음");
      }
    } catch (err) {
      console.error("콘텐츠 로드 실패:", err);
      setScheduleItems([]);
    }

    // 캠페인 선택 시 duration 설정 (스크립트는 콘텐츠 선택 시에만 생성)
    const targetDuration = campaign.target_duration || 180;

    console.log(
      `📊 목표 분량: ${targetDuration}초 (${Math.floor(targetDuration / 60)}분 ${targetDuration % 60}초)`,
    );

    // ✅ Blocks 시스템으로 전환 완료 - duration 설정
    console.log("📝 캠페인 duration 설정:", targetDuration);
    setDuration(targetDuration);

    setWorkflowStep("campaign_loaded"); // 캠페인 로드 완료 상태

    console.log(`✅ 캠페인 로드 완료 - 총 ${targetDuration}초`);

    // 콘텐츠 선택 모달 자동 오픈
    setShowSheetsModal(true);
  };

  return (
    <div className="flex h-screen bg-[#0f1117] text-white overflow-hidden font-inter selection:bg-purple-500/30">
      <StudioSidebar
        selectedCampaignName={selectedCampaign?.name || null}
        onCampaignSelect={handleCampaignSelect}
        onSheetsModalOpen={() => setShowSheetsModal(true)}
        onDriveSelectOpen={() => setShowDriveSelect(true)}
      />

      <div className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(circle_at_50%_0%,rgba(168,85,247,0.08)_0%,transparent_60%)]">
        <StudioHeader
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedCampaignName={selectedCampaign?.name || null}
          onABTestClick={() => setShowABTestModal(true)}
          onExport={() => console.log("Export triggered")}
        />

        {/* ✅ 템플릿 배너 */}
        {templateBannerData && (
          <TemplateBanner
            templateName={templateBannerData.name}
            githubUrl={templateBannerData.githubUrl}
            liveUrl={templateBannerData.liveUrl}
            authorName={templateBannerData.authorName}
            onClose={() => setTemplateBannerData(null)}
          />
        )}

        <main className="flex-1 flex flex-col overflow-hidden relative">
          {/* ✅ 업로드 재료 준비 완료 배너 */}
          {workflowStep === "upload_ready" && (
            <div className="flex items-center gap-3 px-6 py-3 bg-brand-primary-500/10 border-b border-brand-primary-500/20 text-sm">
              <div className="w-2 h-2 rounded-full bg-brand-primary-400 animate-pulse" />
              <span className="text-brand-primary-300 font-bold">
                목소리 + PDF 등록 완료 —{" "}
                {searchParams.get("presentation_id") && `슬라이드 ID: ${searchParams.get("presentation_id")?.slice(0, 12)}...`}
                {searchParams.get("voice_id") && `  ·  목소리 ID: ${searchParams.get("voice_id")?.slice(0, 12)}...`}
              </span>
              <span className="ml-auto text-white/30 text-xs">스크립트 생성 후 영상을 렌더링하세요</span>
            </div>
          )}

          <div className="flex-1 overflow-hidden relative">
            {activeTab === "preview" && (
              <StudioPreview
                workflowStep={workflowStep}
                videoUrl={videoUrl || null}
                isPlaying={isPlaying}
                setIsPlaying={setIsPlaying}
                currentTime={currentTime}
              />
            )}

            {activeTab === "script" && (
              <div className="h-full flex flex-col pt-10">
                <div className="flex-1 overflow-y-auto px-12 custom-scrollbar pb-20">
                  <div className="max-w-4xl mx-auto space-y-10">
                    <div className="flex items-end justify-between border-b border-white/5 pb-8">
                      <div>
                        <h2 className="text-3xl font-black font-outfit text-white mb-2 tracking-tight">대본 마스터링</h2>
                        <p className="text-gray-500 font-medium">VREW 스타일의 컨텍스트 블록 에디터 시스템</p>
                      </div>
                    </div>
                    <BlockList
                      blocks={blocks}
                      selectedBlockId={selectedBlockId}
                      onBlockSelect={setSelectedBlockId}
                      onBlockUpdate={(id, updates) => setBlocks(prev => utilUpdateBlock(prev, id, updates))}
                      onBlockDelete={(id) => setBlocks(prev => utilDeleteBlock(prev, id))}
                      onBlockDuplicate={duplicateBlock}
                      onBlockReorder={setBlocks}
                    />
                    <div className="pt-10">
                      <AddBlockButton onAdd={(type) => setBlocks(prev => utilAddBlock(prev, type))} className="max-w-xl mx-auto" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "storyboard" && (
              <div className="h-full p-12 overflow-y-auto custom-scrollbar">
                <div className="max-w-screen-xl mx-auto">
                  <h2 className="text-4xl font-black font-outfit premium-gradient-text mb-12 tracking-tighter uppercase italic">VISUAL FLOW</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    {blocks.map((block) => (
                      <div
                        key={block.id}
                        onClick={() => setSelectedBlockId(block.id)}
                        className={`premium-card rounded-[2rem] p-6 transition-all cursor-pointer group ${selectedBlockId === block.id ? "ring-2 ring-brand-primary-500 bg-brand-primary-500/[0.03]" : "border-white/5 bg-white/[0.02]"}`}
                      >
                        <div className="aspect-video bg-[#0a0a0c] rounded-2xl mb-6 flex items-center justify-center border border-white/5">
                          <ImageIcon className="w-12 h-12 text-white/5" />
                        </div>
                        <div className="flex items-center gap-3 mb-4">
                          <span className={`px-3 py-1 rounded-full text-[9px] font-black text-white uppercase tracking-widest ${block.type === 'hook' ? 'bg-red-500' : block.type === 'body' ? 'bg-blue-600' : 'bg-green-600'}`}>
                            {block.type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400 leading-relaxed truncate">{block.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <StudioTimeline
            blocks={blocks}
            selectedBlockId={selectedBlockId}
            onBlockSelect={setSelectedBlockId}
            audioUrl={audioUrl}
            currentTime={currentTime}
            onTimeUpdate={setCurrentTime}
            totalDuration={getTotalDuration(blocks)}
          />
        </main>
      </div>

      <StudioInspector
        selectedBlock={blocks.find(b => b.id === selectedBlockId) || null}
        onBlockUpdate={(id, updates) => setBlocks(prev => prev.map(b => b.id === id ? { ...b, ...updates } : b))}
        onAutoSplit={(id) => autoSplitBlock(id)}
        blockCount={blocks.length}
        totalDuration={getTotalDuration(blocks)}
      />

      {/* 모달 영역 */}
      {showSheetsModal && (
        <div className="fixed inset-0 bg-[#000]/90 backdrop-blur-[50px] flex items-center justify-center z-[100] p-8">
          <div className="bg-[#0f0f12] rounded-[3rem] border border-white/10 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl relative">
            <div className="p-12 border-b border-white/5 flex items-center justify-between">
              <div>
                <h2 className="text-4xl font-black font-outfit premium-gradient-text mb-2 tracking-tighter uppercase italic">Asset Library</h2>
                <p className="text-sm text-gray-500 font-bold uppercase tracking-widest">Select your narrative orchestrator</p>
              </div>
              <button onClick={() => setShowSheetsModal(false)} className="p-4 bg-white/5 hover:bg-white/10 rounded-3xl transition-all"><X className="w-8 h-8 text-gray-400" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-12 custom-scrollbar">
              {loading ? (
                <div className="h-64 flex flex-col items-center justify-center gap-6 text-brand-primary-400 animate-pulse font-bold tracking-widest">데이터 동기화 중...</div>
              ) : scheduleItems.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {scheduleItems.map((item, idx) => (
                    <div key={idx} onClick={() => applyScheduleToTimeline(item)} className="premium-card rounded-[2rem] p-8 border-white/5 hover:border-brand-primary-500/50 cursor-pointer transition-all active:scale-95">
                      <h4 className="font-black text-xl mb-2">{item["소제목"]}</h4>
                      <p className="text-[10px] text-gray-600 font-black uppercase tracking-widest">{item["플랫폼"]} • {item["캠페인명"]}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                  <p className="text-gray-500 font-bold">불러올 수 있는 스케쥴이 없습니다.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showABTestModal && (
        <div className="fixed inset-0 bg-black/95 backdrop-blur-[100px] flex items-center justify-center z-[150] p-12">
          <div className="w-full max-w-6xl h-full bg-[#0a0a0c] rounded-[4rem] border border-white/10 overflow-hidden relative shadow-2xl">
            <div className="absolute top-8 right-8 z-[200]">
              <button onClick={() => setShowABTestModal(false)} className="p-4 bg-white/5 hover:bg-white/10 rounded-3xl transition-all"><X className="w-8 h-8" /></button>
            </div>
            <div className="h-full overflow-y-auto custom-scrollbar">
              <ABTestManager contentId={currentContentId} onClose={() => setShowABTestModal(false)} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Suspense로 감싼 메인 컴포넌트
export default function StudioPage() {
  return (
    <AppShell>
      <Suspense fallback={
        <div className="flex h-[calc(100vh-64px)] bg-[#0f1117] text-white items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 border-4 border-brand-primary-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-gray-400 font-medium">Loading Studio...</p>
          </div>
        </div>
      }>
        <StudioPageContent />
      </Suspense>
    </AppShell>
  );
}
