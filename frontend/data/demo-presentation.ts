/**
 * 데모 프리젠테이션 데이터
 *
 * Fresh Food Scaling Architecture PDF (11 슬라이드)
 * 남성 보이스 / 전문적 톤 시나리오
 */

import type { SlideInfo, Presentation } from "@/lib/types/presentation";
import { PresentationStatus } from "@/lib/types/presentation";

export interface VoiceConfig {
  gender: "male" | "female";
  tone: "professional" | "friendly" | "educational";
  language: string;
  voiceLabel: string;
  speed: number;
  targetDurationPerSlide: number;
}

export const DEMO_VOICE_CONFIG: VoiceConfig = {
  gender: "male",
  tone: "professional",
  language: "ko",
  voiceLabel: "남성 (프로페셔널)",
  speed: 1.0,
  targetDurationPerSlide: 20,
};

export const DEMO_SLIDES: SlideInfo[] = [
  {
    slide_number: 1,
    image_path: "/demo/slides/slide-01.png",
    script:
      "안녕하세요. 오늘은 신선식품 이커머스의 새로운 기준에 대해 말씀드리겠습니다. 파이썬 자동화 물류와 B2B 스케일업 아키텍처, 이 두 가지 핵심 축이 어떻게 신선식품 이커머스의 판도를 바꾸고 있는지 함께 살펴보겠습니다.",
    duration: 18.5,
    start_time: 0,
    end_time: 18.5,
  },
  {
    slide_number: 2,
    image_path: "/demo/slides/slide-02.png",
    script:
      "먼저 큰 그림을 보겠습니다. 왼쪽의 물류 자동화 엔진은 Python과 Rails를 통해 100% 무인 데이터 동기화를 실현합니다. 오른쪽의 B2B 성장 플랫폼은 도매와 정기 구독을 위한 맞춤형 커머스를 제공합니다. 핵심은 단일 진실 공급원, 즉 SSOT를 기반으로 백엔드 효율성이 프론트엔드 비즈니스 확장을 주도한다는 점입니다.",
    duration: 23.0,
    start_time: 18.5,
    end_time: 41.5,
  },
  {
    slide_number: 3,
    image_path: "/demo/slides/slide-03.png",
    script:
      "전체 풀필먼트 루프를 보시겠습니다. 주문 통합 수집에서 시작합니다. Python 에이전트가 쿠팡과 네이버의 신규 주문을 자동으로 크롤링합니다. 수집된 데이터는 Rails API와 SQLite를 통해 냉장 창고 발주 양식으로 자동 생성됩니다. 창고에서 출고와 송장 데이터가 업로드되면, 다시 Python 에이전트가 각 쇼핑몰에 배송 처리를 자동으로 역전송합니다. 완전한 순환 구조입니다.",
    duration: 25.0,
    start_time: 41.5,
    end_time: 66.5,
  },
  {
    slide_number: 4,
    image_path: "/demo/slides/slide-04.png",
    script:
      "Step 1을 자세히 살펴보겠습니다. Python 에이전트가 주기적으로 각 쇼핑몰에서 신규 주문을 스크래핑합니다. 수집된 데이터는 SQLite에 즉시 적재되고, 냉장 창고 발주 양식이 엑셀로 원클릭 생성됩니다. 사람의 개입 없이 주문 접수부터 발주까지 전 과정이 자동으로 이루어집니다.",
    duration: 20.0,
    start_time: 66.5,
    end_time: 86.5,
  },
  {
    slide_number: 5,
    image_path: "/demo/slides/slide-05.png",
    script:
      "다음으로 Step 2와 3입니다. 먼저 냉장 창고 소통 부분입니다. 대표님은 Rails에서 생성된 엑셀을 창고에 전달만 하면 됩니다. 그리고 원클릭 업로드, 창고에서 전달받은 송장 엑셀을 Rails에 업로드하면, DB 입력 즉시 Python 에이전트가 각 쇼핑몰에 접속하여 배송 중 처리를 자동으로 완료합니다. 물리적 물류와 디지털 송장이 완벽하게 동기화됩니다.",
    duration: 24.0,
    start_time: 86.5,
    end_time: 110.5,
  },
  {
    slide_number: 6,
    image_path: "/demo/slides/slide-06.png",
    script:
      "이제 왜 자체 B2B 몰이 필요한지 비교해보겠습니다. 배송비 로직을 보면, 레거시 플랫폼은 단순 고정 배송비입니다. 반면 자체 B2B 몰은 박스당 배송비, 일정 금액 이상 무료 등 신선식품에 특화된 로직을 적용할 수 있습니다. 가격 정책 역시 단일 공개 가격이 아닌 사업자 등급제 기반의 히든 가격을 노출합니다. 반복 매출도 매번 수동 재주문이 아닌 정기 구독 결제가 탑재됩니다.",
    duration: 26.0,
    start_time: 110.5,
    end_time: 136.5,
  },
  {
    slide_number: 7,
    image_path: "/demo/slides/slide-07.png",
    script:
      "자체 B2B 몰의 세 가지 핵심 기능을 소개합니다. 첫째, 지능형 물류비 계산입니다. 신선식품 물류비 특성을 반영한 자동 계산기가 탑재되어 있습니다. 둘째, 사업자 전용 히든 프라이싱입니다. B2B 파트너가 로그인했을 때만 도매가와 등급별 가격이 노출됩니다. 셋째, 자동 정기 구독 결제입니다. 카페 등 고정 수요처를 위해 매주 망고, 두리안 자동 결제 시스템이 작동합니다.",
    duration: 25.0,
    start_time: 136.5,
    end_time: 161.5,
  },
  {
    slide_number: 8,
    image_path: "/demo/slides/slide-08.png",
    script:
      "이미지 에셋 관리도 중요합니다. Rails 서버가 원본 고화질 이미지와 영상을 중앙 집중화하여 보관합니다. 그리고 각 쇼핑몰 규격에 맞춘 상세페이지 HTML 템플릿을 Rails에서 자동 생성합니다. 이를 통해 관리 리소스를 최소화하면서도 브랜드 일관성을 유지할 수 있습니다.",
    duration: 19.0,
    start_time: 161.5,
    end_time: 180.5,
  },
  {
    slide_number: 9,
    image_path: "/demo/slides/slide-09.png",
    script:
      "구매 전환율을 높이기 위한 모듈화된 신뢰 지표입니다. 상세페이지 상단에 세 가지 모듈을 배치합니다. 통관 서류로 합법적이고 안전한 수입 절차를 증명합니다. 당도 측정표로 객관적 데이터 기반의 품질을 보증합니다. 산지 직송 영상으로 현지의 신선함을 시각적으로 전달합니다. 이 세 가지를 상단에 모듈화하여 고객 신뢰도를 즉각적으로 확보합니다.",
    duration: 24.0,
    start_time: 180.5,
    end_time: 204.5,
  },
  {
    slide_number: 10,
    image_path: "/demo/slides/slide-10.png",
    script:
      "이커머스 플라이휠을 보겠습니다. 무인 주문 수집이 정확한 창고 소통을 만들고, 정확한 창고 소통이 완벽한 B2B 고객 경험으로 이어집니다. 이것이 구독 증가를 촉진하고, 다시 무인 주문 수집으로 돌아옵니다. 물류 자동화 Steps 1에서 3으로 확보된 시간과 리소스가, 수동 관리 없이 대규모 B2B 정기 구독을 감당할 수 있는 인프라가 됩니다.",
    duration: 23.0,
    start_time: 204.5,
    end_time: 227.5,
  },
  {
    slide_number: 11,
    image_path: "/demo/slides/slide-11.png",
    script:
      "마지막 슬라이드입니다. 파이썬과 Rails로 구축된 자체 아키텍처는 단순한 툴이 아닙니다. 신선식품 이커머스의 게임 체인저입니다. 이 그래프가 보여주듯, 인력 증가 없이 기하급수적 성장이 가능합니다. 물류 자동화, B2B 스케일링, 그리고 운영 탁월성. 이 세 가지가 여러분의 신선식품 이커머스를 새로운 차원으로 이끌 것입니다. 감사합니다.",
    duration: 22.0,
    start_time: 227.5,
    end_time: 249.5,
  },
];

export function getDemoPresentation(
  status: PresentationStatus = PresentationStatus.UPLOADED
): Presentation {
  const now = new Date().toISOString();

  const slides: SlideInfo[] = DEMO_SLIDES.map((slide) => {
    switch (status) {
      case PresentationStatus.UPLOADED:
        return {
          slide_number: slide.slide_number,
          image_path: slide.image_path,
          script: null,
          duration: null,
          start_time: null,
          end_time: null,
        };
      case PresentationStatus.SCRIPT_GENERATED:
        return {
          slide_number: slide.slide_number,
          image_path: slide.image_path,
          script: slide.script,
          duration: slide.duration,
          start_time: null,
          end_time: null,
        };
      default:
        return { ...slide };
    }
  });

  const fullScript =
    status !== PresentationStatus.UPLOADED
      ? DEMO_SLIDES.map((s) => s.script).join("\n\n")
      : null;

  return {
    presentation_id: "demo_fresh_food_001",
    project_id: "demo_project",
    pdf_path: "/demo/Fresh_Food_Scaling_Architecture.pdf",
    total_slides: 11,
    slides,
    full_script: fullScript,
    audio_path:
      status === PresentationStatus.AUDIO_GENERATED ||
      status === PresentationStatus.TIMING_ANALYZED ||
      status === PresentationStatus.VIDEO_READY
        ? "/demo/audio/narration.mp3"
        : null,
    video_path:
      status === PresentationStatus.VIDEO_READY
        ? "/demo/video/presentation.mp4"
        : null,
    status,
    created_at: now,
    updated_at: now,
    metadata: {
      voice_config: DEMO_VOICE_CONFIG,
      source: "demo",
    },
  };
}
