"""
LLM Profile — OpenAI / Anthropic / LangChain 호출 옵션의 단일 진실 소스 (SoT)

ISS-044 (Pattern A 2번째 적용 — ffmpeg_profile.py 다음):
ISS-042에서 도출한 4개 패턴(Atomic Option Group / Compositional Helpers /
Variant via Parameter, Not Branch / Verifier Co-located)을 LLM 호출 영역에 적용.

배경:
    backend/app/services 안의 LLM 호출은 3가지 분기로 흩어져 있음:
        1. OpenAI SDK 직접 (openai package) — 7개 파일
        2. Anthropic SDK 직접 (anthropic package) — 1개 파일 (strategy_agent)
        3. LangChain ChatOpenAI/ChatAnthropic — 5개 파일

    각 호출 사이트가 model 이름·temperature·max_tokens·system_prompt를
    하드코딩하면 — 모델 가격 변동·새 모델 출시·태스크별 튜닝 시
    여러 파일을 동시에 수정해야 함 (회귀 위험).

원칙:
    1. 호출 사이트는 "task"만 알면 된다 (모델/온도/토큰은 모듈이 결정)
    2. 백엔드 분기(OpenAI/Anthropic/LangChain)는 모듈 안에서 처리
    3. 모델 가격·이름은 단일 상수 테이블에 산다 (ISS-040 cost model 연동)
    4. task별 프리셋이 시간에 따라 변경되면 이 한 파일만 수정한다

태스크 카탈로그 (ISS-040 cost model 기준):
    - writer            : Master Script 작성 (GPT-4o, temp=0.7)
    - writer_creative   : 컨셉/슬로건 작성 (GPT-4o, temp=0.9)
    - critic            : 일반 검증 (GPT-4o-mini, temp=0.0)
    - compliance        : 컴플라이언스 검증 (GPT-4o-mini, temp=0.0)
    - slot_filler       : 슬롯 변수 채움 (GPT-4o-mini, temp=0.0)
    - vision_correction : OCR GPT-4 Vision 보정 (GPT-4o, temp=0.3)
    - thumbnail_analyze : 썸네일 분석 (GPT-4o, temp=0.2)
    - continuity        : 콘티 일관성 (Claude Haiku, temp=0.3)
    - slide_to_script   : 슬라이드→스크립트 (Claude Haiku, temp=0.7)
    - long_form         : 긴 콘텐츠 (Claude Sonnet, temp=0.7)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

# ─────────────────────────────────────────────────────────────────────────────
# 모델 상수 (ISS-040 cost model 연동)
# ─────────────────────────────────────────────────────────────────────────────

# OpenAI 모델
GPT_4O = "gpt-4o"
GPT_4O_MINI = "gpt-4o-mini"
GPT_4 = "gpt-4"  # legacy, 새 코드에서 사용 금지

# Anthropic 모델
CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"

# 모델별 가격 (USD per 1M tokens, ISS-040 cost model)
MODEL_PRICING = {
    GPT_4O: {"input": 2.50, "output": 10.00},
    GPT_4O_MINI: {"input": 0.15, "output": 0.60},
    GPT_4: {"input": 30.00, "output": 60.00},  # legacy, 비싸므로 회피
    CLAUDE_3_HAIKU: {"input": 0.25, "output": 1.25},
    CLAUDE_3_5_SONNET: {"input": 3.00, "output": 15.00},
}

# 1 USD ≈ 1400 KRW (대략, 가격 표시용)
USD_TO_KRW = 1400


# ─────────────────────────────────────────────────────────────────────────────
# Task 프리셋 (단일 진실 소스)
# ─────────────────────────────────────────────────────────────────────────────

# Task 이름 타입 (autocomplete/lint 친화)
TaskName = Literal[
    "writer",
    "writer_creative",
    "critic",
    "compliance",
    "slot_filler",
    "vision_correction",
    "thumbnail_analyze",
    "continuity",
    "slide_to_script",
    "long_form",
]


@dataclass(frozen=True)
class TaskPreset:
    """Task별 LLM 옵션 묶음 (Atomic Option Group)."""
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str
    backend: Literal["openai", "anthropic", "langchain_openai", "langchain_anthropic"]
    timeout_seconds: int = 60
    retry_attempts: int = 3
    response_format: Optional[str] = None  # "json_object" 등


# 모든 task 프리셋의 단일 카탈로그.
# 변경 시 이 dict만 수정하면 모든 호출 사이트가 자동 반영됨.
TASK_PRESETS: dict[TaskName, TaskPreset] = {
    "writer": TaskPreset(
        model=GPT_4O,
        temperature=0.7,
        max_tokens=2000,
        system_prompt=(
            "당신은 OmniVibe Pro의 Master Script Writer입니다. "
            "1인 마케팅 에이전시의 거래처(병원·학원·마트 등)를 위해 "
            "60초 영상 스크립트를 작성합니다. 한국어 평어체, "
            "확신 있는 톤, 추상어 금지(혁신/차세대/솔루션 등). "
            "숫자와 검증 가능한 사실로 말합니다."
        ),
        backend="openai",
    ),
    "writer_creative": TaskPreset(
        model=GPT_4O,
        temperature=0.9,
        max_tokens=1500,
        system_prompt=(
            "당신은 컨셉·슬로건·Hook 카피 전문가입니다. "
            "5초 안에 시선을 사로잡는 첫 문장을 만듭니다."
        ),
        backend="openai",
    ),
    "critic": TaskPreset(
        model=GPT_4O_MINI,
        temperature=0.0,
        max_tokens=800,
        system_prompt=(
            "당신은 결과물 검증자입니다. 주어진 텍스트가 요청 조건을 "
            "만족하는지 객관적으로 판단하고 위반 사항만 출력합니다."
        ),
        backend="openai",
    ),
    "compliance": TaskPreset(
        model=GPT_4O_MINI,
        temperature=0.0,
        max_tokens=1000,
        system_prompt=(
            "당신은 의료·학원·식품·금융 광고법 전문 검증자입니다. "
            "주어진 광고 카피가 다음 룰을 위반하는지 판단합니다: "
            "(1) 효과 단언 (2) 비교 우위 (3) 보장 표현 (4) 의무 표시 누락. "
            "위반 시 정확한 룰 ID와 대체 표현을 제시합니다."
        ),
        backend="openai",
        response_format="json_object",
    ),
    "slot_filler": TaskPreset(
        model=GPT_4O_MINI,
        temperature=0.0,
        max_tokens=500,
        system_prompt=(
            "당신은 변수 슬롯 채우기 전문가입니다. "
            "주어진 슬롯 카탈로그와 거래처 데이터를 받아 정확한 값으로 "
            "치환합니다. 추측 금지, 데이터에 없는 값은 빈 문자열."
        ),
        backend="openai",
    ),
    "vision_correction": TaskPreset(
        model=GPT_4O,
        temperature=0.1,  # 원본 ocr_vision_corrector.py의 의도 보존 (정확성 우선)
        max_tokens=2000,
        system_prompt=(
            "당신은 OCR 보정 전문가입니다. Tesseract OCR 결과의 "
            "오인식·줄바꿈 오류·한자/한글 혼동을 이미지를 보고 "
            "정확하게 보정합니다. 원본의 의미와 구조를 보존합니다."
        ),
        backend="openai",
    ),
    "thumbnail_analyze": TaskPreset(
        model=GPT_4O,
        temperature=0.2,
        max_tokens=1500,
        system_prompt=(
            "당신은 YouTube 썸네일 성과 분석가입니다. "
            "썸네일 이미지를 분석하여 시각적 요소·텍스트 가독성·"
            "감정 hook·CTR 예측을 객관적으로 평가합니다."
        ),
        backend="openai",
    ),
    "continuity": TaskPreset(
        model=CLAUDE_3_HAIKU,
        temperature=0.3,
        max_tokens=4096,
        system_prompt=(
            "당신은 영상 콘티 일관성 검증자입니다. "
            "장면 간 연결, 캐릭터 일관성, 톤 유지를 검증합니다."
        ),
        backend="langchain_anthropic",
    ),
    "slide_to_script": TaskPreset(
        model=CLAUDE_3_HAIKU,
        temperature=0.7,
        max_tokens=4096,
        system_prompt=(
            "당신은 슬라이드 → 영상 스크립트 변환기입니다. "
            "각 슬라이드의 핵심 메시지를 구어체 나레이션으로 변환합니다. "
            "시간 제약: 슬라이드당 약 10초 분량 (한글 25~35자)."
        ),
        backend="langchain_anthropic",
    ),
    "long_form": TaskPreset(
        model=CLAUDE_3_5_SONNET,
        temperature=0.7,
        max_tokens=8000,
        system_prompt=(
            "당신은 장문 콘텐츠 작성자입니다. "
            "3~10분 영상을 위한 깊이 있는 스크립트를 작성합니다."
        ),
        backend="langchain_anthropic",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 옵션 args 생성 (Pattern A: Atomic Option Group)
# ─────────────────────────────────────────────────────────────────────────────

def llm_safe_chat_kwargs(
    task: TaskName,
    *,
    user_message: str,
    extra_messages: Optional[list[dict]] = None,
    override_temperature: Optional[float] = None,
    override_max_tokens: Optional[int] = None,
    override_system_prompt: Optional[str] = None,
) -> dict[str, Any]:
    """
    OpenAI SDK chat.completions.create() 에 그대로 전달 가능한 kwargs.

    원자적 옵션 묶음:
        - model
        - temperature
        - max_tokens
        - messages (system + user)
        - response_format (compliance 등에 자동)

    호출 사이트는 task만 지정하면 됨. 모델/온도/시스템 프롬프트는 모듈이 결정.

    예시:
        kwargs = llm_safe_chat_kwargs("writer", user_message=prompt)
        response = await client.chat.completions.create(**kwargs)
    """
    preset = TASK_PRESETS[task]
    if preset.backend not in ("openai", "langchain_openai"):
        raise ValueError(
            f"Task '{task}' uses backend '{preset.backend}'. "
            f"Use llm_safe_anthropic_kwargs() or llm_safe_langchain_chat() instead."
        )

    system_prompt = override_system_prompt or preset.system_prompt
    messages = [{"role": "system", "content": system_prompt}]
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": user_message})

    kwargs: dict[str, Any] = {
        "model": preset.model,
        "messages": messages,
        "temperature": override_temperature if override_temperature is not None else preset.temperature,
        "max_tokens": override_max_tokens or preset.max_tokens,
    }
    if preset.response_format:
        kwargs["response_format"] = {"type": preset.response_format}
    return kwargs


def llm_safe_anthropic_kwargs(
    task: TaskName,
    *,
    user_message: str,
    extra_messages: Optional[list[dict]] = None,
    override_temperature: Optional[float] = None,
    override_max_tokens: Optional[int] = None,
) -> dict[str, Any]:
    """
    Anthropic SDK messages.create() 에 그대로 전달 가능한 kwargs.

    Anthropic은 system을 별도 파라미터로 받음 (messages 안에 안 들어감).
    """
    preset = TASK_PRESETS[task]
    if preset.backend not in ("anthropic", "langchain_anthropic"):
        raise ValueError(
            f"Task '{task}' uses backend '{preset.backend}'. "
            f"Use llm_safe_chat_kwargs() instead."
        )

    messages = []
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": user_message})

    return {
        "model": preset.model,
        "system": preset.system_prompt,
        "messages": messages,
        "temperature": override_temperature if override_temperature is not None else preset.temperature,
        "max_tokens": override_max_tokens or preset.max_tokens,
    }


def llm_safe_langchain_chat_kwargs(
    task: TaskName,
    *,
    override_temperature: Optional[float] = None,
    override_max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    LangChain ChatOpenAI / ChatAnthropic 생성자에 전달할 kwargs.

    이 함수는 task의 backend가 무엇이든 LangChain wrapper로 호출 가능하게 함
    (실용성 우선 — director_agent 같은 LangChain 전용 코드 호환).

    api_key 주입 규칙:
        - 모델 이름이 'gpt-' 또는 'claude-'로 시작하는지 보고 적절한 키 이름 선택

    예시:
        from langchain_anthropic import ChatAnthropic
        kwargs = llm_safe_langchain_chat_kwargs("writer", api_key=settings.OPENAI_API_KEY)
        llm = ChatOpenAI(**kwargs)
    """
    preset = TASK_PRESETS[task]
    base: dict[str, Any] = {
        "model": preset.model,
        "temperature": override_temperature if override_temperature is not None else preset.temperature,
        "max_tokens": override_max_tokens or preset.max_tokens,
    }
    if api_key:
        # 모델 prefix로 provider 추정 (backend 필드보다 우선)
        if preset.model.startswith("gpt-") or preset.backend in ("openai", "langchain_openai"):
            base["openai_api_key"] = api_key
        elif preset.model.startswith("claude-") or preset.backend in ("anthropic", "langchain_anthropic"):
            base["anthropic_api_key"] = api_key
    return base


def get_system_prompt(task: TaskName, override: Optional[str] = None) -> str:
    """task별 시스템 프롬프트 조회 (LangChain prompt 빌더용)."""
    if override:
        return override
    return TASK_PRESETS[task].system_prompt


def get_model_name(task: TaskName) -> str:
    """task별 모델 이름 조회 (로그·메트릭용)."""
    return TASK_PRESETS[task].model


# ─────────────────────────────────────────────────────────────────────────────
# 비용 계산 (Pattern B: Compositional Helper)
# ─────────────────────────────────────────────────────────────────────────────

def estimate_cost_usd(
    task: TaskName,
    *,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    호출 비용 추정 (USD).
    ISS-040 cost model 연동.
    """
    preset = TASK_PRESETS[task]
    pricing = MODEL_PRICING.get(preset.model)
    if not pricing:
        return 0.0
    cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
    return round(cost, 6)


def estimate_cost_krw(
    task: TaskName,
    *,
    input_tokens: int,
    output_tokens: int,
) -> int:
    """호출 비용 추정 (KRW). ISS-040 cost model 단가."""
    usd = estimate_cost_usd(task, input_tokens=input_tokens, output_tokens=output_tokens)
    return round(usd * USD_TO_KRW)


# ─────────────────────────────────────────────────────────────────────────────
# 검증 함수 (Pattern D: Verifier Co-located with Generator)
# ─────────────────────────────────────────────────────────────────────────────

def verify_llm_response(
    task: TaskName,
    response_text: str,
    *,
    require_json: Optional[bool] = None,
    min_length: int = 1,
    max_length: Optional[int] = None,
) -> dict[str, Any]:
    """
    LLM 응답이 task 기대 형식을 만족하는지 검증.

    Returns:
        {"ok": bool, "errors": [...], "checks": {...}}
    """
    import json as json_lib

    preset = TASK_PRESETS[task]
    errors: list[str] = []
    checks: dict[str, Any] = {}

    # 길이 검증
    text_len = len(response_text)
    checks["length"] = text_len
    if text_len < min_length:
        errors.append(f"response too short: {text_len} < {min_length}")
    if max_length and text_len > max_length:
        errors.append(f"response too long: {text_len} > {max_length}")

    # JSON 형식 검증 (preset 또는 override)
    expects_json = require_json
    if expects_json is None:
        expects_json = preset.response_format == "json_object"
    if expects_json:
        try:
            json_lib.loads(response_text)
            checks["json_valid"] = True
        except Exception as e:
            errors.append(f"expected JSON but parse failed: {e}")
            checks["json_valid"] = False

    # 빈 응답
    if not response_text.strip():
        errors.append("empty response")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "checks": checks,
        "task": task,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 모듈 인트로스펙션 (디버깅/문서화)
# ─────────────────────────────────────────────────────────────────────────────

def list_tasks() -> list[str]:
    """등록된 모든 task 이름."""
    return sorted(TASK_PRESETS.keys())


def task_info(task: TaskName) -> dict[str, Any]:
    """task의 설정 정보 (로그/디버깅용, system_prompt 첫 100자만)."""
    preset = TASK_PRESETS[task]
    return {
        "task": task,
        "model": preset.model,
        "backend": preset.backend,
        "temperature": preset.temperature,
        "max_tokens": preset.max_tokens,
        "system_prompt_preview": preset.system_prompt[:100] + ("..." if len(preset.system_prompt) > 100 else ""),
        "response_format": preset.response_format,
        "model_pricing_per_1m": MODEL_PRICING.get(preset.model),
    }
