"use client";

import { useState, useEffect } from "react";
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
} from "lucide-react";
import ClientsList from "@/components/ClientsList";
import AudioWaveform from "@/components/AudioWaveform";
import BlockListPanel from "@/components/BlockListPanel";
import {
  ScriptBlock,
  splitScriptIntoBlocks,
  reorderBlocks,
} from "@/lib/blocks/types";
import { Button } from "@/components/ui/Button";
import ABTestManager from "@/components/ABTestManager";

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

export default function StudioPage() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(180); // 기본 180초 (3분)
  const [selectedSection, setSelectedSection] = useState<number | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(
    null,
  );
  const [showSheetsModal, setShowSheetsModal] = useState(false);
  const [showContentCreateForm, setShowContentCreateForm] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [loading, setLoading] = useState(false);
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

  // 레거시: sections state (호환성 유지)
  const [sections, setSections] = useState<any[]>([]);

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

  // A/B 테스트 모달 상태
  const [showABTestModal, setShowABTestModal] = useState(false);

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

  const reorderBlocksByDragDrop = (reorderedBlocks: ScriptBlock[]) => {
    // 드래그 앤 드롭으로 순서 변경 시, 타이밍 자동 재계산
    setBlocks(reorderBlocks(reorderedBlocks));
  };

  // 스케줄 불러오기
  const loadSchedule = async (spreadsheetId: string) => {
    try {
      const res = await fetch(
        `/api/sheets-schedule?spreadsheet_id=${spreadsheetId}`,
      );
      const data = await res.json();

      if (data.success) {
        // 선택된 캠페인에 속한 콘텐츠만 필터링
        let filteredSchedule = data.schedule;

        if (selectedCampaign) {
          filteredSchedule = data.schedule.filter(
            (item: any) => item["캠페인명"] === selectedCampaign.name,
          );
          console.log(
            `📋 "${selectedCampaign.name}" 캠페인 콘텐츠: ${filteredSchedule.length}개`,
          );
        }

        setScheduleItems(filteredSchedule);
        console.log(
          "✅ SQLite에서 로드된 캠페인:",
          filteredSchedule.length,
          "개",
        );
      } else {
        console.error("❌ 스케줄 로드 실패:", data.message);
      }
    } catch (err) {
      console.error("❌ 스케줄 로드 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  // 스케줄 항목 선택하여 타임라인에 적용
  const applyScheduleToTimeline = async (item: any) => {
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
            `http://localhost:8000/api/v1/storyboard/campaigns/${selectedCampaign?.id}/content/${item.id}/generate`,
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
        setSelectedSection(1); // 첫 번째 섹션 자동 선택
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
      // 전체 스크립트 결합 (모든 섹션)
      const fullScript = sections.map((s) => s.script).join("\n\n");

      if (!fullScript.trim()) {
        alert("스크립트가 비어있습니다");
        setWorkflowStep("script_ready");
        return;
      }

      // Audio API 호출 (Celery 비동기 처리)
      const res = await fetch("http://localhost:8000/api/v1/audio/generate", {
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

        // 상태 폴링 (5초마다 확인)
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(
              `http://localhost:8000/api/v1/audio/status/${data.task_id}`,
            );
            const statusData = await statusRes.json();

            console.log(`🔄 오디오 생성 상태: ${statusData.status}`);

            if (statusData.status === "SUCCESS" && statusData.result) {
              clearInterval(pollInterval);

              // 실제 파일 경로 저장 (Director Agent에서 사용)
              const audioPath = statusData.result.audio_path;
              setAudioUrl(audioPath);

              console.log(`✅ 오디오 생성 완료: ${audioPath}`);
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
        }, 5000);
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
      const fullScript = sections.map((s) => s.script).join("\n\n");

      // Director Agent API 호출 (비동기 작업)
      const res = await fetch(
        "http://localhost:8000/api/v1/director/generate-video",
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
              `http://localhost:8000/api/v1/director/task-status/${data.task_id}`,
            );
            const statusData = await statusRes.json();

            console.log(
              `🔄 영상 생성 상태: ${statusData.status} (${statusData.progress?.toFixed(1)}%)`,
            );

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
                setVideoUrl(`http://localhost:8000${videoPath}`);
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
  const handleCampaignSelect = (campaign: Campaign) => {
    console.log("🎯 캠페인 선택됨:", campaign);

    setSelectedCampaign(campaign);

    // 캠페인 선택 시 기본 스크립트 로드
    const targetDuration = campaign.target_duration || 180;

    console.log(
      `📊 목표 분량: ${targetDuration}초 (${Math.floor(targetDuration / 60)}분 ${targetDuration % 60}초)`,
    );

    const newSections = [
      {
        id: 1,
        type: "훅",
        duration: Math.round(targetDuration * 0.15), // 15%
        color: "bg-red-500",
        script: `안녕하세요! ${campaign.name}에 대해 알아보겠습니다.`,
      },
      {
        id: 2,
        type: "본문",
        duration: Math.round(targetDuration * 0.7), // 70%
        color: "bg-blue-500",
        script:
          '여기에 본문 스크립트를 작성하세요. 우측 패널에서 직접 수정하거나, "구글 시트 연동" 버튼으로 AI 스크립트를 자동 생성할 수 있습니다.',
      },
      {
        id: 3,
        type: "CTA",
        duration: Math.round(targetDuration * 0.15), // 15%
        color: "bg-green-500",
        script: "좋아요와 구독 부탁드립니다!",
      },
    ];

    console.log("📝 생성된 섹션:", newSections);

    setSections(newSections);
    setDuration(targetDuration);
    setSelectedSection(1); // 첫 번째 섹션 자동 선택
    setWorkflowStep("campaign_loaded"); // 캠페인 로드 완료 상태

    console.log(`✅ 타임라인 업데이트 완료 - 총 ${targetDuration}초`);

    // 콘텐츠 선택 모달 자동 오픈
    setShowSheetsModal(true);
  };

  return (
    <div className="h-screen bg-[#1a1a1a] text-white flex flex-col overflow-hidden">
      {/* 상단 헤더 */}
      <header className="h-14 bg-surface-darkest border-b border-gray-800 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <h1 className="heading-3 bg-gradient-to-r from-brand-primary-400 to-brand-secondary-600 bg-clip-text text-transparent">
            OmniVibe Pro
          </h1>
          <span className="text-sm text-gray-400">|</span>
          <span className="body text-gray-300">
            {selectedCampaign ? selectedCampaign.name : "새 프로젝트"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowABTestModal(true)}
            variant="secondary"
            size="sm"
            className="flex items-center gap-2"
            disabled={!currentContentId}
            title={!currentContentId ? "먼저 콘텐츠를 선택하세요" : "A/B 테스트 관리"}
          >
            <BarChart3 className="w-4 h-4" />
            A/B 테스트
          </Button>
          <Button
            variant="secondary"
            size="sm"
            className="flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            저장
          </Button>
          <Button
            variant="primary"
            size="sm"
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            내보내기
          </Button>
        </div>
      </header>

      {/* 메인 컨텐츠 영역 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 좌측 패널 - 클라이언트 & 캠페인 */}
        <aside className="w-64 bg-[#2a2a2a] border-r border-gray-800 flex flex-col">
          <div className="p-4 border-b border-gray-800">
            <Button
              onClick={() => setShowSheetsModal(true)}
              variant="primary"
              size="sm"
              className="w-full flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z" />
              </svg>
              구글 시트 연동
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <ClientsList onCampaignSelect={handleCampaignSelect} />
          </div>

          <div className="p-4 border-t border-gray-800">
            <h3 className="text-xs font-semibold text-gray-400 mb-2">
              빠른 미디어
            </h3>
            <div className="space-y-2">
              <button className="w-full p-2 border-2 border-dashed border-gray-700 rounded-lg hover:border-gray-600 transition-colors">
                <Upload className="w-4 h-4 mx-auto mb-1 text-gray-500" />
                <p className="text-xs text-gray-500">파일 추가</p>
              </button>
            </div>
          </div>
        </aside>

        {/* 중앙 영역 */}
        <div className="flex-1 flex flex-col">
          {/* 워크플로우 진행 상태 */}
          {workflowStep && (
            <div className="bg-[#2a2a2a] border-b border-gray-800 p-4">
              <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-300">
                    🎬 제작 진행 상황
                  </h3>
                  <div className="text-xs text-gray-400">
                    {workflowStep === "script_generating" ||
                    workflowStep === "script_ready" ||
                    workflowStep === "campaign_loaded"
                      ? "1/3 단계"
                      : workflowStep === "audio_generating" ||
                          workflowStep === "audio_ready"
                        ? "2/3 단계"
                        : "3/3 단계"}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-4">
                  <div
                    className="h-full bg-gradient-to-r from-purple-600 to-pink-600 transition-all duration-500"
                    style={{
                      width:
                        workflowStep === "script_generating"
                          ? "10%"
                          : workflowStep === "script_ready" ||
                              workflowStep === "campaign_loaded"
                            ? "33%"
                            : workflowStep === "audio_generating"
                              ? "50%"
                              : workflowStep === "audio_ready"
                                ? "66%"
                                : workflowStep === "video_rendering"
                                  ? "85%"
                                  : workflowStep === "video_ready"
                                    ? "100%"
                                    : "0%",
                    }}
                  ></div>
                </div>

                {/* 진행 단계 표시 */}
                <div className="flex items-center gap-2 mb-4">
                  {/* 1. 스크립트 생성 */}
                  <div
                    className={`flex-1 px-4 py-2 rounded-lg text-center text-sm font-semibold transition-all ${
                      workflowStep === "script_generating"
                        ? "bg-purple-600 animate-pulse"
                        : workflowStep === "script_ready" ||
                            workflowStep === "audio_generating" ||
                            workflowStep === "audio_ready" ||
                            workflowStep === "video_rendering" ||
                            workflowStep === "video_ready"
                          ? "bg-green-600"
                          : "bg-gray-700"
                    }`}
                  >
                    {workflowStep === "script_generating"
                      ? "📝 스크립트 생성 중..."
                      : "✅ 스크립트 완료"}
                  </div>

                  <div className="text-gray-600">→</div>

                  {/* 2. 오디오 생성 */}
                  <div
                    className={`flex-1 px-4 py-2 rounded-lg text-center text-sm font-semibold transition-all ${
                      workflowStep === "audio_generating"
                        ? "bg-blue-600 animate-pulse"
                        : workflowStep === "audio_ready" ||
                            workflowStep === "video_rendering" ||
                            workflowStep === "video_ready"
                          ? "bg-green-600"
                          : "bg-gray-700"
                    }`}
                  >
                    {workflowStep === "audio_generating"
                      ? "🎤 오디오 생성 중..."
                      : workflowStep === "audio_ready" ||
                          workflowStep === "video_rendering" ||
                          workflowStep === "video_ready"
                        ? "✅ 오디오 완료"
                        : "⏳ 오디오 대기"}
                  </div>

                  <div className="text-gray-600">→</div>

                  {/* 3. 영상 렌더링 */}
                  <div
                    className={`flex-1 px-4 py-2 rounded-lg text-center text-sm font-semibold transition-all ${
                      workflowStep === "video_rendering"
                        ? "bg-red-600 animate-pulse"
                        : workflowStep === "video_ready"
                          ? "bg-green-600"
                          : "bg-gray-700"
                    }`}
                  >
                    {workflowStep === "video_rendering"
                      ? "🎬 영상 렌더링 중..."
                      : workflowStep === "video_ready"
                        ? "✅ 영상 완료"
                        : "⏳ 렌더링 대기"}
                  </div>
                </div>

                {/* 액션 버튼 */}
                <div className="flex gap-2">
                  {workflowStep === "campaign_loaded" && (
                    <div className="flex items-center gap-3 w-full">
                      <div className="flex-1 px-4 py-3 bg-green-600/20 border border-green-600 rounded-lg">
                        <p className="text-green-400 font-semibold text-sm">
                          ✅ 캠페인 &quot;{selectedCampaign?.name}&quot; 로드
                          완료!
                        </p>
                        <p className="text-gray-300 text-xs mt-1">
                          총 {Math.floor(duration / 60)}분 {duration % 60}초
                          분량의 스크립트가 생성되었습니다. 우측 패널에서
                          편집하거나, 아래 버튼으로 AI 스크립트를 자동
                          생성하세요.
                        </p>
                      </div>
                      <button
                        onClick={() => setShowSheetsModal(true)}
                        className="px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold transition-colors whitespace-nowrap"
                      >
                        🪄 AI 스크립트 생성
                      </button>
                      <button
                        onClick={() => setSelectedSection(1)}
                        className="px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors whitespace-nowrap"
                      >
                        ✏️ 직접 작성
                      </button>
                    </div>
                  )}
                  {workflowStep === "script_ready" && (
                    <>
                      {/* 캐시 인디케이터 */}
                      {scriptCached && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-green-600/20 border border-green-600 rounded-lg text-xs">
                          <span className="text-green-400">
                            💾 저장된 스크립트 사용
                          </span>
                          {scriptLoadedAt && (
                            <span className="text-gray-400">
                              (
                              {new Date(scriptLoadedAt).toLocaleTimeString(
                                "ko-KR",
                              )}
                              )
                            </span>
                          )}
                        </div>
                      )}

                      <button
                        onClick={generateAudio}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition-colors"
                      >
                        🔵 오디오 생성하기
                      </button>
                      <button
                        onClick={() => setSelectedSection(1)}
                        className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-sm font-semibold transition-colors"
                      >
                        📝 스크립트 수정
                      </button>
                      {scriptCached && (
                        <button
                          onClick={regenerateScript}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold transition-colors"
                        >
                          🔄 스크립트 재생성
                        </button>
                      )}
                    </>
                  )}
                  {workflowStep === "audio_ready" && (
                    <button
                      onClick={renderVideo}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-semibold transition-colors"
                    >
                      🎬 영상 렌더링 시작
                    </button>
                  )}
                  {workflowStep === "video_ready" && videoUrl && (
                    <div className="flex items-center gap-2">
                      <span className="text-green-400 font-semibold">
                        🎉 영상이 준비되었습니다!
                      </span>
                      <a
                        href={videoUrl}
                        download
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold transition-colors inline-flex items-center"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        다운로드
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 미리보기 영역 */}
          <div className="flex-1 bg-[#0f0f0f] flex items-center justify-center p-4">
            <div className="relative w-full max-w-4xl aspect-video bg-black rounded-lg overflow-hidden shadow-2xl">
              {/* 비디오 플레이어 영역 */}
              {workflowStep === "video_ready" && videoUrl ? (
                // ✅ 영상 준비 완료 시: 실제 비디오 플레이어 표시
                <video
                  className="absolute inset-0 w-full h-full object-contain"
                  controls
                  autoPlay
                  src={videoUrl}
                >
                  <source src={videoUrl} type="video/mp4" />
                  비디오를 재생할 수 없습니다.
                </video>
              ) : (
                // ❌ 영상 준비 전: 플레이스홀더 표시
                <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-900 to-black">
                  <div className="text-center w-full max-w-md px-6">
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-purple-600/20 flex items-center justify-center">
                      <Play className="w-10 h-10 text-purple-400" />
                    </div>
                    <p className="text-gray-400 mb-6">
                      {workflowStep === "script_generating"
                        ? "스크립트 생성 중..."
                        : workflowStep === "script_ready"
                          ? "스크립트 완료. 오디오를 생성하세요"
                          : workflowStep === "audio_generating"
                            ? "오디오 생성 중..."
                            : workflowStep === "audio_ready"
                              ? "오디오 완료. 영상을 렌더링하세요"
                              : workflowStep === "video_rendering"
                                ? "영상 렌더링 중..."
                                : "미리보기 준비 중"}
                    </p>

                    {/* 🎬 영상 렌더링 진행률 표시 */}
                    {workflowStep === "video_rendering" && (
                      <div className="space-y-3">
                        {/* 진행률 바 */}
                        <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-300"
                            style={{ width: `${renderProgress}%` }}
                          />
                        </div>

                        {/* 진행률 숫자 및 상태 메시지 */}
                        <div className="flex items-center justify-between text-xs text-gray-400">
                          <span className="font-semibold text-purple-400">
                            {renderProgress}% 완료
                          </span>
                          <span className="text-gray-500 text-center flex-1">
                            {renderStatus}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 재생 컨트롤 오버레이 - video_ready 상태일 때는 숨김 (네이티브 컨트롤 사용) */}
              {workflowStep !== "video_ready" && (
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                  <div className="flex items-center gap-4">
                    <button
                      className="p-2 hover:bg-white/10 rounded-full transition-colors"
                      disabled
                    >
                      <SkipBack className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="p-3 bg-purple-600/50 rounded-full transition-colors cursor-not-allowed"
                      disabled
                    >
                      <Play className="w-6 h-6" />
                    </button>
                    <button
                      className="p-2 hover:bg-white/10 rounded-full transition-colors"
                      disabled
                    >
                      <SkipForward className="w-5 h-5" />
                    </button>

                    <div className="flex-1 flex items-center gap-2">
                      <span className="text-sm text-gray-300 w-12">0:00</span>
                      <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-600"
                          style={{ width: "0%" }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-300 w-12">0:23</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 타임라인 영역 */}
          <div className="h-64 bg-[#2a2a2a] border-t border-gray-800 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-300">
                타임라인 & 콘티
              </h3>
              <div className="flex items-center gap-2">
                <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs transition-colors">
                  확대
                </button>
                <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs transition-colors">
                  축소
                </button>
              </div>
            </div>

            {/* 타임라인 트랙 */}
            <div className="space-y-2">
              {/* 시간 눈금 - 화면 너비에 맞춤 */}
              <div className="h-6 bg-[#1a1a1a] rounded flex items-center justify-between px-2">
                {(() => {
                  // duration에 따라 적절한 눈금 개수 결정
                  const tickCount = Math.min(Math.ceil(duration / 30), 20);
                  return Array.from({ length: tickCount + 1 }).map((_, i) => {
                    const timeInSeconds = Math.round(
                      (duration / tickCount) * i,
                    );
                    const minutes = Math.floor(timeInSeconds / 60);
                    const seconds = timeInSeconds % 60;
                    return (
                      <div
                        key={i}
                        className="text-xs text-gray-500 whitespace-nowrap"
                      >
                        {minutes}:{seconds.toString().padStart(2, "0")}
                      </div>
                    );
                  });
                })()}
              </div>

              {/* 비디오 트랙 */}
              <div className="relative h-16 bg-[#1a1a1a] rounded overflow-hidden">
                <div className="absolute inset-0 flex">
                  {(() => {
                    // 600초를 기준 스케일로 고정
                    const TIMELINE_BASE = 600;
                    const totalDuration = sections.reduce(
                      (sum, s) => sum + s.duration,
                      0,
                    );

                    return sections.map((section) => {
                      // 각 섹션의 실제 시간을 600초 기준으로 스케일링
                      const widthPercent =
                        (section.duration / TIMELINE_BASE) * 100;
                      const minWidthPx = 80; // 최소 너비 보장
                      console.log(
                        `섹션 ${section.type}: ${section.duration}초 → ${widthPercent.toFixed(2)}% (기준: ${TIMELINE_BASE}초)`,
                      );

                      return (
                        <div
                          key={section.id}
                          onClick={() => setSelectedSection(section.id)}
                          title={`${section.type} - ${section.duration}초 (${widthPercent.toFixed(1)}%)`}
                          className={`${section.color} ${
                            selectedSection === section.id
                              ? "opacity-100 ring-2 ring-white scale-105 z-10 shadow-lg"
                              : "opacity-50 hover:opacity-80 hover:scale-102"
                          } cursor-pointer transition-all duration-200 flex items-center justify-center text-xs font-semibold border-r border-black/30 relative group`}
                          style={{
                            width: `${widthPercent}%`,
                            minWidth: `${minWidthPx}px`,
                          }}
                        >
                          <span className="truncate px-2">
                            {section.type} ({section.duration}s)
                          </span>
                          {/* Hover Tooltip */}
                          <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-3 py-2 rounded-lg text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 shadow-xl">
                            <div className="font-semibold">{section.type}</div>
                            <div className="text-gray-300">
                              {section.duration}초 ({widthPercent.toFixed(1)}%)
                            </div>
                            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>

              {/* 오디오 트랙 - AudioWaveform 컴포넌트 */}
              <div className="relative">
                <div className="absolute left-0 top-0 h-full flex items-center px-4 text-xs font-semibold text-gray-400 bg-[#1a1a1a] border-r border-gray-700 z-10 rounded-l">
                  <Volume2 className="w-4 h-4 text-blue-400" />
                </div>
                <div className="ml-20">
                  <AudioWaveform
                    audioUrl={audioUrl}
                    duration={duration}
                    onTimeUpdate={setCurrentTime}
                    className="h-20"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 우측 패널 - 블록 목록 (VREW 스타일) */}
        <BlockListPanel
          blocks={blocks}
          selectedBlockId={selectedBlockId}
          onAddBlock={addBlock}
          onSelectBlock={setSelectedBlockId}
          onUpdateBlock={updateBlock}
          onDeleteBlock={deleteBlock}
          onDuplicateBlock={duplicateBlock}
          onMoveBlockUp={moveBlockUp}
          onMoveBlockDown={moveBlockDown}
          onReorderBlocks={reorderBlocksByDragDrop}
        />

      </div>

      {/* 캠페인 선택 모달 */}
      {showSheetsModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#2a2a2a] rounded-2xl border border-gray-700 w-full max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
            {/* 모달 헤더 */}
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  <svg
                    className="w-6 h-6 text-purple-500"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z" />
                  </svg>
                  콘텐츠 선택
                </h2>
                <button
                  onClick={() => {
                    setShowSheetsModal(false);
                    setShowSchedule(false);
                    setConnectionResult(null);
                  }}
                  className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              {selectedCampaign && (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <span>캠페인:</span>
                  <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded">
                    {selectedCampaign.name}
                  </span>
                </div>
              )}
            </div>

            {/* 모달 본문 */}
            <div className="flex-1 overflow-y-auto p-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mb-4"></div>
                  <p className="text-gray-400">캠페인 로드 중...</p>
                </div>
              ) : scheduleItems.length > 0 ? (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold">
                      📅 콘텐츠 목록 ({scheduleItems.length}개)
                    </h3>
                    <button
                      onClick={() =>
                        alert("새 콘텐츠 추가 기능은 곧 구현됩니다!")
                      }
                      className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm flex items-center gap-1 transition-colors"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M12 5v14M5 12h14" />
                      </svg>
                      새 콘텐츠
                    </button>
                  </div>

                  <div className="space-y-3">
                    {scheduleItems.map((item: any, index: number) => (
                      <div
                        key={index}
                        onClick={() => applyScheduleToTimeline(item)}
                        className="p-4 bg-[#1a1a1a] border border-gray-700 rounded-lg hover:border-purple-500 cursor-pointer transition-all group"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-white mb-1 group-hover:text-purple-400 transition-colors">
                              {item["소제목"]}
                            </h4>
                            <p className="text-sm text-gray-400 mb-2">
                              {item["캠페인명"]} | {item["플랫폼"]} |{" "}
                              {item["발행일"] || "미정"}
                            </p>
                            {item["주제"] && (
                              <p className="text-xs text-gray-500">
                                주제: {item["주제"]}
                              </p>
                            )}
                          </div>
                          <div className="text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity">
                            →
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : showContentCreateForm ? (
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">
                      새 콘텐츠 추가
                    </h3>
                    <button
                      onClick={() => {
                        setShowContentCreateForm(false);
                        setNewContent({
                          title: "",
                          platform: "Youtube",
                          publish_date: "",
                          topic: "",
                        });
                      }}
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    {/* 소제목 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        소제목 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={newContent.title}
                        onChange={(e) =>
                          setNewContent({
                            ...newContent,
                            title: e.target.value,
                          })
                        }
                        placeholder="예: 시각장애인을 위한 AI 기술의 발전"
                        className="w-full px-4 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                      />
                    </div>

                    {/* 플랫폼 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        플랫폼
                      </label>
                      <select
                        value={newContent.platform}
                        onChange={(e) =>
                          setNewContent({
                            ...newContent,
                            platform: e.target.value,
                          })
                        }
                        className="w-full px-4 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                      >
                        <option value="Youtube">Youtube</option>
                        <option value="Instagram">Instagram</option>
                        <option value="TikTok">TikTok</option>
                        <option value="Facebook">Facebook</option>
                      </select>
                    </div>

                    {/* 발행일 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        발행일
                      </label>
                      <input
                        type="date"
                        value={newContent.publish_date}
                        onChange={(e) =>
                          setNewContent({
                            ...newContent,
                            publish_date: e.target.value,
                          })
                        }
                        className="w-full px-4 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                      />
                    </div>

                    {/* 주제 */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        주제
                      </label>
                      <input
                        type="text"
                        value={newContent.topic}
                        onChange={(e) =>
                          setNewContent({
                            ...newContent,
                            topic: e.target.value,
                          })
                        }
                        placeholder="예: AI 기술"
                        className="w-full px-4 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                      />
                    </div>
                  </div>

                  <div className="flex gap-3 pt-4 border-t border-gray-700">
                    <button
                      onClick={handleCreateContent}
                      disabled={!newContent.title.trim()}
                      className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed rounded-lg text-sm font-semibold transition-colors"
                    >
                      콘텐츠 추가
                    </button>
                    <button
                      onClick={() => {
                        setShowContentCreateForm(false);
                        setNewContent({
                          title: "",
                          platform: "Youtube",
                          publish_date: "",
                          topic: "",
                        });
                      }}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                    >
                      취소
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="w-16 h-16 mb-4 rounded-full bg-gray-700/50 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="32"
                      height="32"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="text-gray-500"
                    >
                      <path d="M3 7v10c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2Z" />
                      <path d="M12 11v6M9 14h6" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {selectedCampaign
                      ? `"${selectedCampaign.name}"에 콘텐츠가 없습니다`
                      : "콘텐츠가 없습니다"}
                  </h3>
                  <p className="text-sm text-gray-400 mb-6 text-center max-w-md">
                    이 캠페인에 첫 번째 콘텐츠를 추가하거나,
                    <br />
                    다른 캠페인을 선택해보세요.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setShowContentCreateForm(true)}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M12 5v14M5 12h14" />
                      </svg>
                      새 콘텐츠 추가
                    </button>
                    <button
                      onClick={() => {
                        setShowSheetsModal(false);
                      }}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                    >
                      다른 캠페인 선택
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* A/B 테스트 모달 */}
      {showABTestModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <ABTestManager
              contentId={currentContentId}
              onClose={() => setShowABTestModal(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
