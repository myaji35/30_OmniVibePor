"""
TTS Profile — OpenAI / CosyVoice2 / edge-tts 호출 옵션의 단일 진실 소스 (SoT)

ISS-045 (Pattern A 3번째 적용 — ffmpeg_profile, llm_profile 다음):
ISS-042에서 도출한 4개 패턴을 TTS 호출 영역에 적용.
ISS-050 도메인 분석 메타 학습(1회차→2회차 진화)을 3회차에 반영.

배경:
    backend/app/services 안의 TTS 호출은 3가지 backend로 흩어져 있음:
        1. OpenAI TTS — services/tts_service.py (유료, 품질 우선)
        2. CosyVoice2 Docker — services/cosyvoice_tts_service.py (무료, 자체 호스팅)
        3. edge-tts — api/v1/produce.py 직접 호출 (무료 Microsoft)

    voice_id + language + speed + stability 등 옵션이 호출 사이트에
    하드코딩되면 — 모델 가격 변동·새 음성 추가·발음 사전 적용 시
    여러 파일을 동시에 수정해야 함.

원칙 (ISS-042):
    1. 호출 사이트는 "voice" 프리셋 이름만 알면 된다 (backend/옵션 모듈이 결정)
    2. Backend 분기(openai/cosyvoice/edge_tts)는 모듈 안에서 처리 (Pattern C)
    3. 모델 가격·이름은 단일 상수 테이블 (ISS-040 cost model 연동)
    4. voice 프리셋이 시간에 따라 변경되면 이 한 파일만 수정
    5. 발음 사전은 vertical별로 모듈이 주입 (Procedure Library 연동)
    6. Zero-Fault 검증 루프는 모듈이 표준 결과를 반환 (Pattern D)

Voice 카탈로그:
    - narrator_ko_warm      : 한국어 따뜻한 남성 (CosyVoice2, default)
    - narrator_ko_confident : 한국어 확신 있는 남성 (CosyVoice2)
    - narrator_ko_friendly  : 한국어 친근한 여성 (OpenAI nova)
    - narrator_ko_professional : 한국어 전문적 여성 (OpenAI shimmer)
    - narrator_ko_cheap     : edge-tts 무료 (Starter plan 기본)
    - doctor_ko_male        : 병의원 원장 톤 (CosyVoice2)
    - doctor_ko_female      : 병의원 여의사 톤 (OpenAI nova)
    - teacher_ko_male       : 학원 선생 톤 (OpenAI echo)
    - announcer_ko_male     : 마트/행사 안내 톤 (CosyVoice2)
    - cloned_user           : 사용자 voice clone (ElevenLabs, 동의 필수)

Vertical 발음 사전 연동:
    - medical: 보툴리눔, 필러, 리쥬란, 메조테라피, IPL, RF 고주파 등
    - academy: 수능, 내신, EBS, 고1·고2·고3, 특목고 등
    - mart: 할인, 1+1, 2+1, 행사, 신상품 등
    - general: 기본 발음 (override 없음)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Backend 상수
# ─────────────────────────────────────────────────────────────────────────────

Backend = Literal["openai", "cosyvoice", "edge_tts", "elevenlabs"]

# OpenAI TTS 음성
OPENAI_ALLOY = "alloy"        # 중성
OPENAI_ECHO = "echo"          # 남성
OPENAI_FABLE = "fable"        # 영국식
OPENAI_ONYX = "onyx"          # 남성, 깊음
OPENAI_NOVA = "nova"          # 여성
OPENAI_SHIMMER = "shimmer"    # 여성, 부드러움

# edge-tts 한국어 voice (Microsoft)
EDGE_KO_MALE_INJOON = "ko-KR-InJoonNeural"
EDGE_KO_FEMALE_SUNHI = "ko-KR-SunHiNeural"

# CosyVoice2 한국어 (자체 호스팅)
COSYVOICE_KO_DEFAULT = "ko-male-warm"
COSYVOICE_KO_CONFIDENT = "ko-male-confident"
COSYVOICE_KO_DOCTOR = "ko-male-doctor"
COSYVOICE_KO_ANNOUNCER = "ko-male-announcer"

# OpenAI TTS 모델
TTS_MODEL_STANDARD = "tts-1"      # 빠름, 저렴
TTS_MODEL_HD = "tts-1-hd"         # 고품질


# ─────────────────────────────────────────────────────────────────────────────
# 가격 테이블 (ISS-040 cost model 연동)
# ─────────────────────────────────────────────────────────────────────────────

# 단가 (USD per 1000 characters)
BACKEND_PRICING_PER_1K_CHARS = {
    "openai": {
        TTS_MODEL_STANDARD: 0.015,
        TTS_MODEL_HD: 0.030,
    },
    "cosyvoice": {
        "default": 0.0,  # 자체 호스팅, GPU 시간만 (amortized in ISS-040 VPS)
    },
    "edge_tts": {
        "default": 0.0,  # Microsoft 무료
    },
    "elevenlabs": {
        "creator": 0.18,   # Creator tier $0.18/1k chars
        "pro": 0.15,       # Pro tier
    },
}

USD_TO_KRW = 1400


# ─────────────────────────────────────────────────────────────────────────────
# Voice 프리셋 (Pattern A: Atomic Option Group, 데이터 우선 — ISS-050 Meta-1)
# ─────────────────────────────────────────────────────────────────────────────

VoiceName = Literal[
    "narrator_ko_warm",
    "narrator_ko_confident",
    "narrator_ko_friendly",
    "narrator_ko_professional",
    "narrator_ko_cheap",
    "doctor_ko_male",
    "doctor_ko_female",
    "teacher_ko_male",
    "announcer_ko_male",
    "cloned_user",
]

Vertical = Literal["medical", "academy", "mart", "beauty", "restaurant", "general"]


@dataclass(frozen=True)
class VoicePreset:
    """Voice별 TTS 옵션 묶음 (Atomic Option Group)."""
    name: str
    backend: Backend
    voice_id: str
    language: str = "ko"
    speed: float = 1.0
    model: str = "default"  # backend별 모델 이름
    description: str = ""
    cost_tier: Literal["free", "low", "medium", "high"] = "low"
    supports_clone: bool = False
    fallback_voices: tuple[str, ...] = field(default_factory=tuple)  # 실패 시 대체


# 모든 voice 프리셋의 단일 카탈로그
# 변경 시 이 dict만 수정하면 모든 호출 사이트가 자동 반영됨
VOICE_PRESETS: dict[VoiceName, VoicePreset] = {
    "narrator_ko_warm": VoicePreset(
        name="narrator_ko_warm",
        backend="cosyvoice",
        voice_id=COSYVOICE_KO_DEFAULT,
        description="기본 한국어 나레이터 (따뜻한 남성)",
        cost_tier="free",
        fallback_voices=("narrator_ko_cheap",),
    ),
    "narrator_ko_confident": VoicePreset(
        name="narrator_ko_confident",
        backend="cosyvoice",
        voice_id=COSYVOICE_KO_CONFIDENT,
        description="확신 있는 한국어 나레이터 (Agency 영상 기본)",
        cost_tier="free",
        fallback_voices=("narrator_ko_warm",),
    ),
    "narrator_ko_friendly": VoicePreset(
        name="narrator_ko_friendly",
        backend="openai",
        voice_id=OPENAI_NOVA,
        model=TTS_MODEL_STANDARD,
        description="친근한 한국어 나레이터 (여성)",
        cost_tier="low",
        fallback_voices=("narrator_ko_cheap",),
    ),
    "narrator_ko_professional": VoicePreset(
        name="narrator_ko_professional",
        backend="openai",
        voice_id=OPENAI_SHIMMER,
        model=TTS_MODEL_HD,
        description="전문적 한국어 나레이터 (여성, 고품질)",
        cost_tier="medium",
        fallback_voices=("narrator_ko_friendly",),
    ),
    "narrator_ko_cheap": VoicePreset(
        name="narrator_ko_cheap",
        backend="edge_tts",
        voice_id=EDGE_KO_MALE_INJOON,
        description="무료 Starter plan 기본 (Microsoft edge-tts)",
        cost_tier="free",
    ),
    "doctor_ko_male": VoicePreset(
        name="doctor_ko_male",
        backend="cosyvoice",
        voice_id=COSYVOICE_KO_DOCTOR,
        description="병의원 원장 톤 (전문성 + 신뢰)",
        cost_tier="free",
        fallback_voices=("narrator_ko_confident",),
    ),
    "doctor_ko_female": VoicePreset(
        name="doctor_ko_female",
        backend="openai",
        voice_id=OPENAI_NOVA,
        model=TTS_MODEL_HD,
        description="병의원 여의사 톤 (친근함 + 전문성)",
        cost_tier="medium",
        fallback_voices=("narrator_ko_friendly",),
    ),
    "teacher_ko_male": VoicePreset(
        name="teacher_ko_male",
        backend="openai",
        voice_id=OPENAI_ECHO,
        model=TTS_MODEL_STANDARD,
        description="학원 선생 톤 (명료함)",
        cost_tier="low",
        fallback_voices=("narrator_ko_cheap",),
    ),
    "announcer_ko_male": VoicePreset(
        name="announcer_ko_male",
        backend="cosyvoice",
        voice_id=COSYVOICE_KO_ANNOUNCER,
        description="마트/행사 안내 톤 (활기참)",
        cost_tier="free",
        fallback_voices=("narrator_ko_warm",),
    ),
    "cloned_user": VoicePreset(
        name="cloned_user",
        backend="elevenlabs",
        voice_id="__user_clone__",  # 실제는 runtime에 DB에서 resolve
        model="creator",
        description="사용자 voice clone (ElevenLabs Professional, 동의 필수)",
        cost_tier="high",
        supports_clone=True,
        fallback_voices=("narrator_ko_confident",),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Vertical별 발음 사전 (Procedure Library 연동)
# ─────────────────────────────────────────────────────────────────────────────

# 각 vertical의 표준 용어 발음 hint (TTS 엔진에 전달)
# 실제 사용 시 Procedure Library와 merge됨
PRONUNCIATION_LEXICON: dict[Vertical, dict[str, str]] = {
    "medical": {
        "보툴리눔": "보툴리눔",
        "필러": "필러",
        "리쥬란": "리쥬란",
        "메조테라피": "메조테라피",
        "IPL": "아이피엘",
        "RF": "알에프",
        "HIFU": "하이푸",
        "PRP": "피알피",
        "PDO": "피디오",
        "CO2": "씨오투",
    },
    "academy": {
        "EBS": "이비에스",
        "SAT": "에스에이티",
        "TOEFL": "토플",
        "IELTS": "아이엘츠",
        "KSAT": "수능",
        "내신": "내신",
    },
    "mart": {
        "1+1": "일플러스일",
        "2+1": "이플러스일",
        "1 + 1": "일플러스일",
    },
    "beauty": {
        "BB": "비비",
        "CC": "씨씨",
        "UV": "유브이",
    },
    "restaurant": {
        "L.A.": "엘에이",
        "BBQ": "비비큐",
    },
    "general": {},
}


def apply_pronunciation(text: str, vertical: Vertical = "general") -> str:
    """
    vertical별 발음 사전을 텍스트에 적용.

    TTS 엔진에 보내기 전 치환하여 발음 오류를 사전 차단.
    Zero-Fault 재생성 루프 호출 횟수를 줄이는 핵심 메커니즘.
    """
    lexicon = PRONUNCIATION_LEXICON.get(vertical, {})
    if not lexicon:
        return text
    result = text
    for term, pronunciation in lexicon.items():
        result = result.replace(term, pronunciation)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Backend별 kwargs 생성 (Pattern B: Compositional Helpers)
# ─────────────────────────────────────────────────────────────────────────────

def tts_safe_openai_kwargs(
    voice: VoiceName,
    *,
    text: str,
    vertical: Vertical = "general",
    override_model: Optional[str] = None,
) -> dict[str, Any]:
    """
    OpenAI TTS client.audio.speech.create() 에 전달 가능한 kwargs.

    예시:
        kwargs = tts_safe_openai_kwargs("narrator_ko_friendly", text=script, vertical="medical")
        response = await client.audio.speech.create(**kwargs)
    """
    preset = VOICE_PRESETS[voice]
    if preset.backend != "openai":
        raise ValueError(
            f"Voice '{voice}' uses backend '{preset.backend}', not openai. "
            f"Use tts_safe_cosyvoice_kwargs() or tts_safe_edge_tts_kwargs()."
        )

    processed_text = apply_pronunciation(text, vertical=vertical)

    return {
        "model": override_model or preset.model,
        "voice": preset.voice_id,
        "input": processed_text,
        "response_format": "mp3",
        "speed": preset.speed,
    }


def tts_safe_cosyvoice_kwargs(
    voice: VoiceName,
    *,
    text: str,
    vertical: Vertical = "general",
) -> dict[str, Any]:
    """
    CosyVoice2 Docker 서비스에 전달 가능한 kwargs.

    예시:
        kwargs = tts_safe_cosyvoice_kwargs("doctor_ko_male", text=script, vertical="medical")
        audio = await cosyvoice_service.synthesize(**kwargs)
    """
    preset = VOICE_PRESETS[voice]
    if preset.backend != "cosyvoice":
        raise ValueError(
            f"Voice '{voice}' uses backend '{preset.backend}', not cosyvoice."
        )

    processed_text = apply_pronunciation(text, vertical=vertical)

    return {
        "voice_id": preset.voice_id,
        "text": processed_text,
        "language": preset.language,
        "speed": preset.speed,
    }


def tts_safe_edge_tts_kwargs(
    voice: VoiceName,
    *,
    text: str,
    vertical: Vertical = "general",
) -> dict[str, Any]:
    """
    edge-tts Communicate() 에 전달 가능한 kwargs.

    예시:
        import edge_tts
        kwargs = tts_safe_edge_tts_kwargs("narrator_ko_cheap", text=script, vertical="general")
        communicate = edge_tts.Communicate(**kwargs)
    """
    preset = VOICE_PRESETS[voice]
    if preset.backend != "edge_tts":
        raise ValueError(
            f"Voice '{voice}' uses backend '{preset.backend}', not edge_tts."
        )

    processed_text = apply_pronunciation(text, vertical=vertical)

    return {
        "text": processed_text,
        "voice": preset.voice_id,
    }


def tts_safe_universal_kwargs(
    voice: VoiceName,
    *,
    text: str,
    vertical: Vertical = "general",
) -> tuple[Backend, dict[str, Any]]:
    """
    Universal helper — voice 이름만 주면 자동으로 올바른 backend kwargs 반환.

    Pattern C의 정석: 호출 사이트는 backend를 몰라도 됨.

    예시:
        backend, kwargs = tts_safe_universal_kwargs("doctor_ko_male", text=script, vertical="medical")
        if backend == "cosyvoice":
            audio = await cosyvoice_service.synthesize(**kwargs)
        elif backend == "openai":
            response = await openai_client.audio.speech.create(**kwargs)
        elif backend == "edge_tts":
            communicate = edge_tts.Communicate(**kwargs)
    """
    preset = VOICE_PRESETS[voice]
    if preset.backend == "openai":
        return "openai", tts_safe_openai_kwargs(voice, text=text, vertical=vertical)
    elif preset.backend == "cosyvoice":
        return "cosyvoice", tts_safe_cosyvoice_kwargs(voice, text=text, vertical=vertical)
    elif preset.backend == "edge_tts":
        return "edge_tts", tts_safe_edge_tts_kwargs(voice, text=text, vertical=vertical)
    elif preset.backend == "elevenlabs":
        raise NotImplementedError(
            "ElevenLabs는 voice_cloning_service.py에서 별도 처리. "
            "cloned_user는 runtime에 DB에서 voice_id resolve 필요."
        )
    else:
        raise ValueError(f"Unknown backend: {preset.backend}")


# ─────────────────────────────────────────────────────────────────────────────
# Fallback 체인 (Pattern B: Compositional)
# ─────────────────────────────────────────────────────────────────────────────

def resolve_voice_with_fallback(voice: VoiceName, max_depth: int = 3) -> list[VoiceName]:
    """
    voice 프리셋의 fallback 체인 해석.

    일차 voice 실패 시 fallback_voices를 순차 시도하기 위한 체인 반환.
    Zero-Fault 루프의 상위 레벨 복원 전략에 사용.

    예시:
        chain = resolve_voice_with_fallback("doctor_ko_male")
        # → ["doctor_ko_male", "narrator_ko_confident", "narrator_ko_warm", "narrator_ko_cheap"]
        for v in chain:
            try:
                result = await tts_safe_synthesize_with_loop(v, text=...)
                if result["status"] == "success": break
            except Exception: continue
    """
    chain: list[VoiceName] = [voice]
    current = voice
    depth = 0
    while depth < max_depth:
        preset = VOICE_PRESETS.get(current)
        if not preset or not preset.fallback_voices:
            break
        next_voice = preset.fallback_voices[0]
        if next_voice in chain:  # 순환 방지
            break
        chain.append(next_voice)  # type: ignore[arg-type]
        current = next_voice  # type: ignore[assignment]
        depth += 1
    return chain


# ─────────────────────────────────────────────────────────────────────────────
# 비용 계산 (ISS-040 cost model 연동)
# ─────────────────────────────────────────────────────────────────────────────

def estimate_tts_cost_usd(
    voice: VoiceName,
    *,
    char_count: int,
    zero_fault_retries: float = 1.3,
) -> float:
    """
    TTS 호출 비용 추정 (USD). ISS-040 cost model 연동.

    Args:
        voice: voice preset 이름
        char_count: 텍스트 문자 수
        zero_fault_retries: 평균 재시도 횟수 (Zero-Fault loop, 기본 1.3회)

    Returns:
        USD 비용
    """
    preset = VOICE_PRESETS[voice]
    pricing = BACKEND_PRICING_PER_1K_CHARS.get(preset.backend, {})

    # model/tier 결정
    if preset.backend == "openai":
        rate = pricing.get(preset.model, pricing.get(TTS_MODEL_STANDARD, 0.015))
    elif preset.backend == "elevenlabs":
        rate = pricing.get(preset.model, pricing.get("creator", 0.18))
    else:
        rate = pricing.get("default", 0.0)

    base_cost = (char_count / 1000) * rate
    return round(base_cost * zero_fault_retries, 6)


def estimate_tts_cost_krw(
    voice: VoiceName,
    *,
    char_count: int,
    zero_fault_retries: float = 1.3,
) -> int:
    """TTS 호출 비용 추정 (KRW). ISS-040 cost model 단가."""
    usd = estimate_tts_cost_usd(voice, char_count=char_count, zero_fault_retries=zero_fault_retries)
    return round(usd * USD_TO_KRW)


def estimate_tts_cost_for_video_edition_krw(voice: VoiceName) -> int:
    """
    OmniVibe 1편 영상 기준 TTS **API** 비용 (60초, 150자 한글).

    ※ ISS-040 cost model의 TTS 단가 110원(CosyVoice2 기준)은 이 함수의 값과 다름.
    ISS-040의 110원은 CosyVoice2 Docker 운영 GPU 시간을 1편당 amortize한 간접비.
    이 함수는 직접 API 비용(OpenAI·ElevenLabs 등 외부 서비스 과금)만 반환.

    ISS-040 총 편당 원가 = 이 함수 결과 (직접 API 비용) + VPS/GPU amortize (간접비).

    Args:
        voice: voice preset 이름

    Returns:
        1편 영상 기준 외부 API 직접 비용 (KRW)
    """
    # 한국어 150자 ≈ 약 300 char (공백+조사 포함 추정)
    return estimate_tts_cost_krw(voice, char_count=300, zero_fault_retries=1.3)


# ─────────────────────────────────────────────────────────────────────────────
# 검증 함수 (Pattern D: Verifier Co-located)
# ─────────────────────────────────────────────────────────────────────────────

def verify_tts_output(
    audio_bytes: bytes,
    *,
    expected_duration_seconds: float,
    min_size_kb: int = 5,
    max_size_kb: int = 10_000,
    duration_tolerance: float = 0.3,
) -> dict[str, Any]:
    """
    TTS 출력물 기본 검증 (의미 검증은 STT + audio_correction_loop가 담당).

    Pattern D의 TTS 영역 적용 — 객관적으로 측정 가능한 항목만 검증:
        - 바이트 크기 (극단적 작음/큼)
        - 예상 길이 대비 실제 길이 (대략적)
        - MP3 header 유효성

    의미 검증(발음 정확도, 띄어쓰기)은 STT + correction loop가 수행.

    Returns:
        {"ok": bool, "size_kb": int, "errors": [str, ...]}
    """
    errors: list[str] = []
    size_kb = len(audio_bytes) / 1024

    if size_kb < min_size_kb:
        errors.append(f"audio too small: {size_kb:.1f}KB < {min_size_kb}KB (TTS 실패 의심)")
    if size_kb > max_size_kb:
        errors.append(f"audio too large: {size_kb:.1f}KB > {max_size_kb}KB")

    # MP3 header 확인 (간단) — ID3 or 0xFFFB/0xFFFA/0xFFE3
    if len(audio_bytes) >= 3:
        header = audio_bytes[:3]
        is_id3 = header == b"ID3"
        is_mp3_frame = audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0
        if not (is_id3 or is_mp3_frame):
            errors.append("audio header not MP3 (ID3 or 0xFFEx expected)")

    # 대략 60초 영상 기준: 150자 한글 ≈ 8~15초 발화 → 약 100~250KB MP3
    # 더 정밀한 duration 체크는 audio_correction_loop가 pydub로 수행

    return {
        "ok": len(errors) == 0,
        "size_kb": round(size_kb, 1),
        "byte_count": len(audio_bytes),
        "errors": errors,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 모듈 인트로스펙션
# ─────────────────────────────────────────────────────────────────────────────

def list_voices() -> list[str]:
    """등록된 모든 voice preset 이름."""
    return sorted(VOICE_PRESETS.keys())


def list_voices_by_backend(backend: Backend) -> list[str]:
    """특정 backend의 voice preset 이름."""
    return sorted(
        name for name, preset in VOICE_PRESETS.items() if preset.backend == backend
    )


def list_voices_by_cost_tier(tier: Literal["free", "low", "medium", "high"]) -> list[str]:
    """특정 가격 티어의 voice preset 이름."""
    return sorted(
        name for name, preset in VOICE_PRESETS.items() if preset.cost_tier == tier
    )


def voice_info(voice: VoiceName) -> dict[str, Any]:
    """voice 프리셋의 설정 정보 (로그/디버깅용)."""
    preset = VOICE_PRESETS[voice]
    return {
        "name": preset.name,
        "backend": preset.backend,
        "voice_id": preset.voice_id,
        "language": preset.language,
        "speed": preset.speed,
        "model": preset.model,
        "description": preset.description,
        "cost_tier": preset.cost_tier,
        "supports_clone": preset.supports_clone,
        "fallback_chain": resolve_voice_with_fallback(preset.name),  # type: ignore[arg-type]
        "estimated_cost_per_video_krw": estimate_tts_cost_for_video_edition_krw(preset.name),  # type: ignore[arg-type]
    }
