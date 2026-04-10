# ISS-039 DOMAIN_ANALYZE: COMPLIANCE_PACK_DSL

> 8개 vertical의 광고법 룰을 YAML DSL로 정의
> 작성일: 2026-04-10 | 상태: DOMAIN_ANALYZE

---

## 1. DSL 스키마 정의

### 1.1 CompliancePack 최상위 구조

```yaml
# backend/compliance_packs/{vertical}/{sub_vertical}.yaml
meta:
  vertical: string           # medical | academy | mart | beauty | restaurant | fitness | realestate | general
  sub_vertical: string       # dermatology | plastic_surgery | dental | default 등
  version: string            # SemVer (1.0.0)
  last_updated: date         # 2026-04-10
  author: string             # 작성자
  law_snapshot_date: date    # 법조항 스냅샷 기준일
  description_ko: string     # 팩 설명

rules: list[Rule]            # 룰 목록

disclaimers:                 # vertical 공통 고지문
  - id: string
    text_ko: string
    required_when: string    # always | contains_price | contains_effect | contains_promotion
```

### 1.2 Rule 스키마

```yaml
Rule:
  id: string                 # {VERT}-{SUB}-{NNN} (예: MED-DERM-001)
  type: enum                 # regex | must_include | must_exclude | llm_semantic
  severity: enum             # critical | warning | info
  enabled: bool              # true (기본값)
  
  # --- type별 필드 ---
  # regex / must_exclude:
  pattern: string            # 정규식 패턴 (Python re 호환)
  
  # must_include:
  required_text: string      # 포함 필수 텍스트
  trigger_when: string       # always | contains_price | contains_effect | contains_before_after | contains_promotion
  
  # llm_semantic:
  prompt_ko: string          # LLM에게 전달할 검증 프롬프트 (한국어)
  examples:                  # Few-shot 예시
    - input: string
      violation: bool
      reason: string
  
  # --- 공통 필드 ---
  message_ko: string         # 위반 시 사용자에게 보여줄 메시지
  law_reference: string      # 법조항 참조 (예: 의료법 제56조 제2항 제1호)
  auto_fix_suggestion: string # Writer Agent에게 전달할 대체 표현 가이드
  tags: list[string]         # 분류 태그 (superlative, price, guarantee, disclaimer 등)
```

### 1.3 룰 타입별 실행 방식

| type | 실행 엔진 | 비용 | 지연 시간 |
|------|----------|------|----------|
| `regex` | Python `re.search()` | 0원 | <1ms |
| `must_exclude` | Python `re.search()` → match이면 위반 | 0원 | <1ms |
| `must_include` | Python `not re.search()` → match 없으면 위반 | 0원 | <1ms |
| `llm_semantic` | LLM API 호출 (Claude Haiku) | ~2원/건 | 500ms~2s |

**실행 순서**: regex/must_exclude/must_include를 먼저 전부 실행 → critical 위반 없으면 llm_semantic 실행.
llm_semantic은 비용이 있으므로 정적 룰로 걸러낸 후에만 호출한다.

### 1.4 디렉토리 구조

```
backend/compliance_packs/
├── schema.yaml              # Rule 스키마 정의 (JSON Schema for validation)
├── medical/
│   ├── dermatology.yaml     # 피부과
│   ├── plastic_surgery.yaml # 성형외과
│   ├── dental.yaml          # 치과
│   └── default.yaml         # 의료 공통
├── academy/
│   └── default.yaml
├── mart/
│   └── default.yaml
├── beauty/
│   └── default.yaml
├── restaurant/
│   └── default.yaml
├── fitness/
│   └── default.yaml
├── realestate/
│   └── default.yaml
└── general/
    └── default.yaml
```

---

## 2. medical-dermatology 룰 (30개)

### 2.1 최상급/과장 표현 금지 (MED-DERM-001 ~ 006)

```yaml
- id: MED-DERM-001
  type: must_exclude
  severity: critical
  pattern: "최고의?|가장 좋은|업계 (최초|1위|넘버원)|No\\.?\\s*1|넘버\\s*원"
  message_ko: "최상급 표현 사용 금지 — 의료법 제56조 위반"
  law_reference: "의료법 제56조 제2항 제1호 (객관적 근거 없는 최상급 표현)"
  auto_fix_suggestion: "효과적인|검증된|전문적인|신뢰할 수 있는"
  tags: [superlative]

- id: MED-DERM-002
  type: must_exclude
  severity: critical
  pattern: "100%|완벽한 (효과|결과|치료)|확실한 효과|반드시 (효과|개선|치료)"
  message_ko: "효과 보장 표현 금지 — 개인차 존재"
  law_reference: "의료법 제56조 제2항 제3호 (치료 효과 보장)"
  auto_fix_suggestion: "높은 만족도를 보이는|개선을 기대할 수 있는"
  tags: [guarantee]

- id: MED-DERM-003
  type: must_exclude
  severity: critical
  pattern: "기적의?|마법같은|획기적(인|인가|으로)|혁명적(인|으로)|놀라운 (효과|변화|결과)"
  message_ko: "과장 표현 금지"
  law_reference: "의료법 제56조 제2항 제1호"
  auto_fix_suggestion: "전문적인 시술을 통한|체계적인 관리를 통한"
  tags: [exaggeration]

- id: MED-DERM-004
  type: must_exclude
  severity: warning
  pattern: "유일(한|하게)|독보적(인|으로)|독점(적|으로)|세계 (최초|유일)"
  message_ko: "근거 없는 유일성 주장 금지"
  law_reference: "의료법 제56조 제2항 제1호"
  auto_fix_suggestion: "전문화된|특화된"
  tags: [superlative]

- id: MED-DERM-005
  type: must_exclude
  severity: warning
  pattern: "즉각적(인|으로)|즉시 (효과|개선|변화)|바로 (효과|변화|개선|달라)"
  message_ko: "즉각적 효과 표현은 오인 유발"
  law_reference: "의료법 제56조 제2항 제3호"
  auto_fix_suggestion: "점진적으로 개선되는|시술 후 회복 기간을 거쳐"
  tags: [guarantee, timeline]

- id: MED-DERM-006
  type: must_exclude
  severity: critical
  pattern: "부작용\\s*(없|제로|0|zero)|안전\\s*100%|무(통증|부작용)|통증\\s*(없|zero|제로|0)"
  message_ko: "부작용/통증 부재 단언 금지"
  law_reference: "의료법 제56조 제2항 제3호"
  auto_fix_suggestion: "부작용이 적은 편이며 개인차가 있을 수 있습니다"
  tags: [safety, guarantee]
```

### 2.2 비포/애프터 및 시각적 오인 (MED-DERM-007 ~ 010)

```yaml
- id: MED-DERM-007
  type: llm_semantic
  severity: critical
  prompt_ko: |
    다음 스크립트에 비포앤애프터(전후 비교) 표현이 포함되어 있는지 판단하세요.
    직접적인 '전/후' 언급뿐 아니라, 시각적 전후 비교를 암시하는 표현도 포함합니다.
    예: "시술 전의 칙칙한 피부가 환하게 변했습니다" → 위반
  examples:
    - input: "시술 전후 사진을 보시면 차이가 확연합니다"
      violation: true
      reason: "비포앤애프터 사진 직접 언급"
    - input: "꾸준한 관리로 피부 상태 개선을 기대할 수 있습니다"
      violation: false
      reason: "전후 비교 없이 일반적인 기대 표현"
  message_ko: "비포앤애프터(전후 비교) 표현 금지 — 의료광고심의위 가이드라인"
  law_reference: "의료법 제56조 제2항 제5호, 의료광고심의기준 제4조"
  auto_fix_suggestion: "치료 효과는 개인마다 다를 수 있습니다. 전문의 상담을 통해 확인하세요."
  tags: [before_after, visual]

- id: MED-DERM-008
  type: must_exclude
  severity: critical
  pattern: "전후\\s*(비교|사진|영상)|비포(\\s*앤?\\s*|\\s*&\\s*)애프터|before\\s*(and|&)?\\s*after|시술\\s*(전|후)\\s*(사진|영상|모습)"
  message_ko: "전후 비교 사진/영상 직접 언급 금지"
  law_reference: "의료법 제56조 제2항 제5호"
  auto_fix_suggestion: "전문의 상담을 통해 기대 효과를 확인하세요"
  tags: [before_after]

- id: MED-DERM-009
  type: must_exclude
  severity: warning
  pattern: "변신|탈바꿈|환골탈태|거듭나|완전히\\s*(달라|변|바뀌)"
  message_ko: "극적 변화를 암시하는 표현 자제"
  law_reference: "의료법 제56조 제2항 제5호"
  auto_fix_suggestion: "피부 상태 개선을 위한 전문적인 관리"
  tags: [before_after, exaggeration]

- id: MED-DERM-010
  type: llm_semantic
  severity: warning
  prompt_ko: |
    다음 스크립트에서 특정 환자의 치료 결과를 일반적인 효과로 오인하게 하는 표현이 있는지 판단하세요.
    예: "저희 병원에서 치료받은 A씨는 2주 만에 완치되었습니다" → 위반 (개별 사례를 일반화)
  examples:
    - input: "많은 환자분들이 3회 시술 후 만족스러운 결과를 경험하셨습니다"
      violation: true
      reason: "개별 경험을 일반적 결과로 표현"
    - input: "개인차가 있으나 평균적으로 3-5회 시술이 권장됩니다"
      violation: false
      reason: "개인차 언급 + 권장 사항으로 표현"
  message_ko: "개별 치료 사례를 일반적 효과로 오인시키는 표현 금지"
  law_reference: "의료법 제56조 제2항 제3호"
  auto_fix_suggestion: "개인차가 있을 수 있으며, 전문의 상담이 필요합니다"
  tags: [testimonial, generalization]
```

### 2.3 가격/할인/이벤트 관련 (MED-DERM-011 ~ 015)

```yaml
- id: MED-DERM-011
  type: must_exclude
  severity: critical
  pattern: "무료\\s*(시술|치료|상담)|공짜|0원\\s*(시술|치료)"
  message_ko: "무료 시술/치료 표현은 과잉 유인 광고에 해당"
  law_reference: "의료법 제56조 제2항 제7호 (과잉 유인)"
  auto_fix_suggestion: "합리적인 비용으로|부담 없는 상담"
  tags: [price, inducement]

- id: MED-DERM-012
  type: must_exclude
  severity: warning
  pattern: "\\d+%\\s*(할인|세일|OFF|오프)|반값|반액|파격\\s*(가격|할인|이벤트)"
  message_ko: "과도한 할인율 강조는 의료 소비자 오인 유발"
  law_reference: "의료법 제56조 제2항 제7호"
  auto_fix_suggestion: "합리적인 비용으로 전문 진료를 받으실 수 있습니다"
  tags: [price, discount]

- id: MED-DERM-013
  type: must_exclude
  severity: warning
  pattern: "선착순|한정\\s*(수량|인원|기간)|마감\\s*임박|오늘만|지금\\s*아니면"
  message_ko: "긴급성/희소성을 이용한 의료소비 유도 금지"
  law_reference: "의료법 제56조 제2항 제7호"
  auto_fix_suggestion: "편하신 시간에 상담을 예약하세요"
  tags: [urgency, inducement]

- id: MED-DERM-014
  type: llm_semantic
  severity: warning
  prompt_ko: |
    다음 스크립트에서 의료 시술의 가격을 비의료 소비재(쇼핑, 외식 등)와 비교하여
    '저렴함'을 강조하는 표현이 있는지 판단하세요.
    예: "명품 가방 하나 값이면 평생 젊어집니다" → 위반
  examples:
    - input: "커피 한 잔 가격으로 피부 관리를 시작하세요"
      violation: true
      reason: "비의료 소비재와 가격 비교"
    - input: "전문의 상담 후 맞춤 치료 계획을 수립합니다"
      violation: false
      reason: "가격 비교 없는 의료 정보 전달"
  message_ko: "의료 시술과 비의료 소비재의 가격 비교 표현 금지"
  law_reference: "의료법 제56조 제2항 제7호"
  auto_fix_suggestion: "합리적인 비용의 맞춤 진료 플랜을 상담해 드립니다"
  tags: [price, comparison]

- id: MED-DERM-015
  type: must_exclude
  severity: warning
  pattern: "경품|사은품|추첨|상품권\\s*증정|포인트\\s*적립|캐시백"
  message_ko: "경품/사은품을 통한 의료소비 유도 금지"
  law_reference: "의료법 제56조 제2항 제7호"
  auto_fix_suggestion: "표현 삭제 — 의료 광고에서 경품 관련 언급 불가"
  tags: [inducement, gift]
```

### 2.4 의료인 자격/경력 관련 (MED-DERM-016 ~ 019)

```yaml
- id: MED-DERM-016
  type: must_exclude
  severity: critical
  pattern: "명의|신의 손|국내 (최고|최상위)\\s*(의사|의료진|전문의)"
  message_ko: "의료인에 대한 근거 없는 최상급 수식어 금지"
  law_reference: "의료법 제56조 제2항 제1호"
  auto_fix_suggestion: "풍부한 경험의 전문의|피부과 전문의"
  tags: [superlative, credential]

- id: MED-DERM-017
  type: llm_semantic
  severity: critical
  prompt_ko: |
    다음 스크립트에서 의사의 학력, 경력, 자격을 허위 또는 과장되게 표현하는 부분이 있는지 판단하세요.
    검증 불가능한 수치(예: "10만 건 이상 시술 경험")나 허위 학위 언급이 해당됩니다.
  examples:
    - input: "하버드 출신 전문의가 직접 시술합니다"
      violation: true
      reason: "실제 학력 검증 불가 — 허위 자격 표시 위험"
    - input: "피부과 전문의가 직접 상담합니다"
      violation: false
      reason: "일반적인 자격 표현"
  message_ko: "의료인 자격/경력에 대한 과장 또는 허위 표현 금지"
  law_reference: "의료법 제56조 제2항 제2호"
  auto_fix_suggestion: "피부과 전문의 직접 진료"
  tags: [credential, false_claim]

- id: MED-DERM-018
  type: must_exclude
  severity: warning
  pattern: "연예인\\s*(전담|담당|피부과)|셀럽|인플루언서\\s*(추천|선택|인정)"
  message_ko: "특정 유명인의 이용 사실을 광고에 활용 금지"
  law_reference: "의료법 제56조 제2항 제4호 (환자 유인)"
  auto_fix_suggestion: "표현 삭제"
  tags: [celebrity, endorsement]

- id: MED-DERM-019
  type: must_exclude
  severity: critical
  pattern: "수술\\s*건수\\s*\\d|시술\\s*(누적|총)\\s*\\d|\\d+\\s*(건|회|례)\\s*(이상\\s*)?(시술|수술|치료)\\s*(경험|달성|완료)"
  message_ko: "검증 불가능한 구체적 시술 건수 주장 금지"
  law_reference: "의료법 제56조 제2항 제2호"
  auto_fix_suggestion: "풍부한 시술 경험을 갖춘 전문의"
  tags: [credential, statistics]
```

### 2.5 부작용/위험성 고지 의무 (MED-DERM-020 ~ 023)

```yaml
- id: MED-DERM-020
  type: must_include
  severity: critical
  required_text: "개인(에 따라|차가|마다)\\s*(차이|다를|있을)"
  trigger_when: contains_effect
  message_ko: "효과 관련 표현 시 '개인차가 있을 수 있습니다' 고지 필수"
  law_reference: "의료법 시행규칙 제33조 (부작용 고지 의무)"
  auto_fix_suggestion: "스크립트 말미에 '개인에 따라 효과에 차이가 있을 수 있습니다' 추가"
  tags: [disclaimer, side_effect]

- id: MED-DERM-021
  type: must_include
  severity: critical
  required_text: "전문의\\s*상담|의사와\\s*상담|전문\\s*상담"
  trigger_when: always
  message_ko: "의료 광고에는 전문의 상담 권유 문구 필수 포함"
  law_reference: "의료법 시행규칙 제33조"
  auto_fix_suggestion: "반드시 전문의와 상담 후 결정하세요"
  tags: [disclaimer, consultation]

- id: MED-DERM-022
  type: must_include
  severity: warning
  required_text: "부작용|주의사항|이상반응"
  trigger_when: contains_effect
  message_ko: "시술 효과 언급 시 부작용/주의사항 안내 권장"
  law_reference: "의료법 시행규칙 제33조"
  auto_fix_suggestion: "시술 후 일시적인 붉어짐, 부기 등이 나타날 수 있으며 전문의 안내에 따라 관리하세요"
  tags: [disclaimer, side_effect]

- id: MED-DERM-023
  type: llm_semantic
  severity: warning
  prompt_ko: |
    다음 스크립트에서 시술의 위험성이나 합병증 가능성을 의도적으로 축소하거나 은폐하는 표현이 있는지 판단하세요.
    예: "간단한 시술이라 걱정 마세요" → 위반 (위험성 축소)
  examples:
    - input: "레이저 시술은 간단해서 일상에 전혀 지장이 없어요"
      violation: true
      reason: "위험성 축소 — 실제로 다운타임 존재"
    - input: "시술 후 개인에 따라 1-3일 정도 붉어짐이 있을 수 있습니다"
      violation: false
      reason: "부작용 적절히 고지"
  message_ko: "시술 위험성 축소/은폐 금지"
  law_reference: "의료법 제56조 제2항 제3호"
  auto_fix_suggestion: "시술에 따른 주의사항은 전문의와 상담하세요"
  tags: [safety, minimization]
```

### 2.6 비교광고/타 의료기관 비하 (MED-DERM-024 ~ 026)

```yaml
- id: MED-DERM-024
  type: must_exclude
  severity: critical
  pattern: "타\\s*(병원|의원|클리닉)(보다|에\\s*비해|과\\s*비교|대비)|다른\\s*(병원|의원)(보다|에\\s*비해)"
  message_ko: "타 의료기관과의 비교 광고 금지"
  law_reference: "의료법 제56조 제2항 제6호 (비교 광고)"
  auto_fix_suggestion: "표현 삭제 — 비교 대상 언급 없이 자체 장점만 서술"
  tags: [comparison, competitor]

- id: MED-DERM-025
  type: must_exclude
  severity: critical
  pattern: "인증(된|받은)\\s*(병원|의원|클리닉)|보건복지부\\s*인증|JCI|국제\\s*인증"
  message_ko: "실제로 보유하지 않은 인증 표시 금지 (확인 필요)"
  law_reference: "의료법 제56조 제2항 제2호"
  auto_fix_suggestion: "인증 보유 여부를 거래처에 확인 후 포함 결정"
  tags: [credential, certification]

- id: MED-DERM-026
  type: must_exclude
  severity: warning
  pattern: "실패\\s*(없|제로)|재시술\\s*불필요|한\\s*번(에|으로)\\s*(끝|해결|완료)"
  message_ko: "재시술 불필요 또는 실패 없음 표현 금지"
  law_reference: "의료법 제56조 제2항 제3호"
  auto_fix_suggestion: "체계적인 치료 계획으로 최적의 결과를 추구합니다"
  tags: [guarantee, exaggeration]
```

### 2.7 신의료기술/미승인 장비 (MED-DERM-027 ~ 028)

```yaml
- id: MED-DERM-027
  type: llm_semantic
  severity: critical
  prompt_ko: |
    다음 스크립트에서 식약처 미승인 의료기기나 신의료기술평가를 받지 않은 시술을
    마치 공인된 것처럼 표현하는 부분이 있는지 판단하세요.
    특정 브랜드 장비명(예: "울쎄라", "써마지", "인모드")이 포함되어 있더라도
    "FDA 승인" 같은 해외 인증만으로 국내 승인인 것처럼 오인시키면 위반입니다.
  examples:
    - input: "FDA 승인받은 최신 장비로 시술합니다"
      violation: true
      reason: "FDA 승인은 국내 식약처 승인과 다름 — 오인 유발"
    - input: "식약처 인증 장비를 사용하여 안전하게 시술합니다"
      violation: false
      reason: "국내 승인 기관 정확히 명시"
  message_ko: "미승인 의료기기/시술을 공인된 것처럼 표현 금지"
  law_reference: "의료법 제56조 제2항 제8호, 의료기기법 제24조"
  auto_fix_suggestion: "전문 장비를 사용한 시술 — 구체적 인증 현황은 거래처 확인 필요"
  tags: [device, approval, false_claim]

- id: MED-DERM-028
  type: must_exclude
  severity: warning
  pattern: "최신\\s*(기술|장비|레이저|기기)|첨단\\s*(의료|장비|기술)|차세대"
  message_ko: "'최신/첨단' 표현은 상대적이므로 구체적 근거 없이 사용 자제"
  law_reference: "의료법 제56조 제2항 제1호"
  auto_fix_suggestion: "전문 장비를 사용한|검증된 장비를 활용한"
  tags: [exaggeration, device]
```

### 2.8 환자 후기/추천 관련 (MED-DERM-029 ~ 030)

```yaml
- id: MED-DERM-029
  type: must_exclude
  severity: critical
  pattern: "환자\\s*(후기|리뷰|추천|평가)|체험(기|담|후기)|\\d+명\\s*(이상\\s*)?(만족|추천|선택)"
  message_ko: "환자 후기/추천을 광고에 활용 금지"
  law_reference: "의료법 제56조 제2항 제4호 (환자 경험담 광고 금지)"
  auto_fix_suggestion: "표현 삭제 — 의료광고에서 환자 후기 인용 불가"
  tags: [testimonial, review]

- id: MED-DERM-030
  type: llm_semantic
  severity: warning
  prompt_ko: |
    다음 스크립트에서 특정 질환의 치료법이 '유일한 해결책'이거나 '이 시술만이 답'이라는
    뉘앙스를 전달하는 표현이 있는지 판단하세요. 의료 소비자의 선택권을 제한하는 표현이 해당됩니다.
  examples:
    - input: "여드름 흉터는 프락셀 레이저만이 유일한 해결책입니다"
      violation: true
      reason: "유일한 해결책 단정"
    - input: "여드름 흉터 개선을 위한 다양한 시술 중 전문의가 맞춤 추천드립니다"
      violation: false
      reason: "다양한 선택지 + 전문의 상담 유도"
  message_ko: "특정 시술만이 유일한 해결책이라는 표현 금지"
  law_reference: "의료법 제56조 제2항 제1호"
  auto_fix_suggestion: "전문의 상담을 통해 가장 적합한 치료 방법을 찾아보세요"

# ── ISS-112 BIZ_VALIDATE P0 보완: 의료법 제57조 사전심의번호 ──
- id: MED-DERM-031
  type: must_include
  severity: critical
  required_text: "심의번호"
  trigger_when: always
  message_ko: "온라인 의료광고는 사전심의번호를 반드시 표기해야 합니다 (의료법 제57조). 심의번호가 없는 의료광고는 위법입니다."
  law_reference: "의료법 제57조 (의료광고의 심의)"
  auto_fix_suggestion: "본 광고는 의료광고심의위원회 심의필 제XXXX호입니다. [실제 심의번호로 교체 필요]"
  tags: [exclusive_claim, choice_restriction]
```

---

## 3. 나머지 7개 vertical 룰

### 3.1 academy (학원) — 10개

```yaml
meta:
  vertical: academy
  sub_vertical: default
  version: "1.0.0"
  law_snapshot_date: 2026-04-10
  description_ko: "학원 광고 컴플라이언스 팩 — 학원법, 표시광고법 기반"

rules:
- id: ACD-001
  type: must_exclude
  severity: critical
  pattern: "합격\\s*(보장|확실|100%)|반드시\\s*합격|불합격\\s*시\\s*(전액|환불)"
  message_ko: "합격 보장 표현 금지"
  law_reference: "표시광고법 제3조 (거짓/과장 광고 금지)"
  auto_fix_suggestion: "합격을 위한 체계적인 커리큘럼"
  tags: [guarantee]

- id: ACD-002
  type: must_exclude
  severity: critical
  pattern: "(합격률|수강생)\\s*\\d+%|\\d+명\\s*(합격|배출)|전원\\s*합격"
  message_ko: "검증 불가 합격률/실적 수치 사용 금지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "체계적인 학습 관리 시스템"
  tags: [statistics, false_claim]

- id: ACD-003
  type: must_exclude
  severity: critical
  pattern: "최고의?\\s*(강사|선생님|교수진)|업계\\s*1위\\s*(학원|강사)|국내\\s*최고"
  message_ko: "최상급 강사 수식어 금지"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "경험 풍부한 전문 강사진"
  tags: [superlative]

- id: ACD-004
  type: must_exclude
  severity: warning
  pattern: "성적\\s*(폭발|급상승|수직\\s*상승)|성적\\s*\\d+점\\s*향상\\s*보장"
  message_ko: "성적 향상 보장/과장 표현 금지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "꾸준한 학습을 통한 실력 향상"
  tags: [guarantee, exaggeration]

- id: ACD-005
  type: must_exclude
  severity: warning
  pattern: "타\\s*(학원|기관)(보다|에\\s*비해|과\\s*비교)|경쟁\\s*(학원|업체)"
  message_ko: "타 학원 비교광고 금지"
  law_reference: "표시광고법 제3조 제1항 제3호 (부당 비교)"
  auto_fix_suggestion: "차별화된 커리큘럼과 전문 강사진"
  tags: [comparison]

- id: ACD-006
  type: must_exclude
  severity: warning
  pattern: "무료\\s*(수강|교재|강의)|0원\\s*(수강|교재)"
  message_ko: "무료 수강 표현 시 조건 미고지는 기만 광고"
  law_reference: "표시광고법 제3조 제1항 제2호 (기만 광고)"
  auto_fix_suggestion: "체험 수업 가능 (조건 별도 안내)"
  tags: [price, inducement]

- id: ACD-007
  type: must_exclude
  severity: critical
  pattern: "선행\\s*학습\\s*(필수|추천)|\\d+학년\\s*선행|초등\\s*\\d학년.*중등\\s*과정"
  message_ko: "과도한 선행학습 조장 표현은 학원법 위반 소지"
  law_reference: "학원법 시행령 제18조 (교습과정 제한)"
  auto_fix_suggestion: "학생 수준에 맞는 맞춤형 커리큘럼"
  tags: [advance_learning]

- id: ACD-008
  type: must_include
  severity: warning
  required_text: "상담|문의"
  trigger_when: contains_price
  message_ko: "수강료 언급 시 정확한 정보 확인 가능 경로 안내 필요"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "정확한 수강료는 상담을 통해 안내받으실 수 있습니다"
  tags: [price, disclaimer]

- id: ACD-009
  type: must_exclude
  severity: warning
  pattern: "대치동|강남\\s*학원.*수준|SKY\\s*(출신|강사)|서울대\\s*(출신|강사)"
  message_ko: "특정 지역/학교를 이용한 권위 부여 표현 자제"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "검증된 전문 강사진의 체계적 수업"
  tags: [credential, authority]

- id: ACD-010
  type: must_exclude
  severity: info
  pattern: "수능\\s*(만점|전교\\s*1등|수석)|올\\s*A|\\d+점\\s*만점"
  message_ko: "특정 학생 성적을 광고에 활용 시 검증 필요"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "학생들의 성장을 함께하는 전문 교육기관"
  tags: [testimonial, statistics]
```

### 3.2 mart (마트/유통) — 7개

```yaml
meta:
  vertical: mart
  sub_vertical: default
  version: "1.0.0"
  description_ko: "마트/유통 광고 컴플라이언스 팩"

rules:
- id: MRT-001
  type: must_exclude
  severity: critical
  pattern: "최저가\\s*(보장|도전)|가격\\s*파괴|업계\\s*최저"
  message_ko: "검증 불가 최저가 표현 금지"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "합리적인 가격"
  tags: [price, superlative]

- id: MRT-002
  type: must_exclude
  severity: warning
  pattern: "원산지.*국내산|100%\\s*(국내산|유기농|친환경)"
  message_ko: "원산지/인증 표기는 실제 확인 후에만 사용 가능"
  law_reference: "농수산물 원산지 표시에 관한 법률 제5조"
  auto_fix_suggestion: "신선한 식재료 — 원산지는 매장에서 확인 가능"
  tags: [origin, certification]

- id: MRT-003
  type: must_include
  severity: warning
  required_text: "행사\\s*기간|기간\\s*한정|~까지"
  trigger_when: contains_promotion
  message_ko: "할인/이벤트 광고 시 행사 기간 명시 필수"
  law_reference: "표시광고법 제3조 제1항 제2호"
  auto_fix_suggestion: "행사 기간: YYYY.MM.DD ~ YYYY.MM.DD (거래처 확인 필요)"
  tags: [promotion, period]

- id: MRT-004
  type: must_exclude
  severity: warning
  pattern: "타\\s*(마트|매장)(보다|에\\s*비해|대비)"
  message_ko: "경쟁 매장 비교 표현 금지"
  law_reference: "표시광고법 제3조 제1항 제3호"
  auto_fix_suggestion: "표현 삭제"
  tags: [comparison]

- id: MRT-005
  type: must_exclude
  severity: critical
  pattern: "유기농(?!.*인증)|무농약(?!.*인증)"
  message_ko: "유기농/무농약 표기는 공인 인증 없이 사용 불가"
  law_reference: "친환경농어업법 제23조"
  auto_fix_suggestion: "친환경 인증 확인은 매장에 문의하세요"
  tags: [certification, organic]

- id: MRT-006
  type: must_exclude
  severity: info
  pattern: "건강에\\s*(좋|최고|필수)|질병\\s*(예방|치료)에\\s*효과"
  message_ko: "식품에 대한 질병 치료/예방 효과 표현 금지"
  law_reference: "식품표시광고법 제8조 제1항"
  auto_fix_suggestion: "신선하고 맛있는 식재료"
  tags: [health_claim]

- id: MRT-007
  type: must_exclude
  severity: warning
  pattern: "\\d+인분\\s*(한정|선착순)|재고\\s*소진\\s*시\\s*종료"
  message_ko: "허위 한정수량/긴급성 유발 표현 주의"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "매장 재고 상황에 따라 변동될 수 있습니다"
  tags: [urgency, scarcity]
```

### 3.3 beauty (뷰티) — 8개

```yaml
meta:
  vertical: beauty
  sub_vertical: default
  version: "1.0.0"
  description_ko: "뷰티(미용실/네일/피부관리) 광고 컴플라이언스 팩"

rules:
- id: BTY-001
  type: must_exclude
  severity: critical
  pattern: "피부\\s*(치료|완치|진단)|질병|질환|아토피\\s*(치료|완치)|여드름\\s*(치료|완치)"
  message_ko: "비의료 뷰티업소에서 의료 행위(치료/진단) 표현 금지"
  law_reference: "의료법 제27조 (무면허 의료행위 금지)"
  auto_fix_suggestion: "피부 관리|피부 케어|피부 컨디션 관리"
  tags: [medical_claim]

- id: BTY-002
  type: must_exclude
  severity: critical
  pattern: "주사|보톡스|필러|레이저\\s*(시술|치료)|의료용"
  message_ko: "비의료 뷰티업소에서 의료시술 관련 표현 금지"
  law_reference: "의료법 제27조"
  auto_fix_suggestion: "전문 뷰티 케어 프로그램"
  tags: [medical_procedure]

- id: BTY-003
  type: must_exclude
  severity: warning
  pattern: "최고의?\\s*(미용|뷰티|헤어)|업계\\s*1위|넘버원"
  message_ko: "최상급 표현 금지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "전문 뷰티 케어"
  tags: [superlative]

- id: BTY-004
  type: must_exclude
  severity: warning
  pattern: "100%\\s*(천연|자연|유기농)|화학\\s*성분\\s*(없|무|제로)"
  message_ko: "화장품 성분에 대한 허위/과장 표현 금지"
  law_reference: "화장품법 제13조 (과대광고 금지)"
  auto_fix_suggestion: "엄선된 성분을 사용한"
  tags: [ingredient, false_claim]

- id: BTY-005
  type: must_exclude
  severity: critical
  pattern: "주름\\s*(제거|완전\\s*제거)|탈모\\s*(치료|완치)|모발\\s*재생"
  message_ko: "의료적 효과를 암시하는 표현 금지"
  law_reference: "화장품법 제13조, 의료법 제27조"
  auto_fix_suggestion: "두피/모발 건강 관리 프로그램"
  tags: [medical_claim, exaggeration]

- id: BTY-006
  type: must_exclude
  severity: warning
  pattern: "전후\\s*(비교|사진)|비포(\\s*앤?\\s*)애프터|시술\\s*전후"
  message_ko: "전후 비교 사진은 오인 유발 — 비의료 업소 특히 주의"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "꾸준한 관리로 건강한 피부/모발을 유지하세요"
  tags: [before_after]

- id: BTY-007
  type: must_include
  severity: info
  required_text: "개인(에 따라|차가|마다)"
  trigger_when: contains_effect
  message_ko: "효과 표현 시 개인차 고지 권장"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "효과는 개인에 따라 차이가 있을 수 있습니다"
  tags: [disclaimer]

- id: BTY-008
  type: must_exclude
  severity: warning
  pattern: "셀럽|연예인\\s*(픽|추천|선택)|\\w+\\s*님\\s*(추천|선택|인정)"
  message_ko: "유명인 추천/보증 표현은 검증 없이 사용 금지"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "전문가의 꼼꼼한 케어"
  tags: [endorsement]
```

### 3.4 restaurant (음식점) — 7개

```yaml
meta:
  vertical: restaurant
  sub_vertical: default
  version: "1.0.0"
  description_ko: "음식점/외식업 광고 컴플라이언스 팩"

rules:
- id: RST-001
  type: must_exclude
  severity: critical
  pattern: "100%\\s*(한우|국내산)|순\\s*(한우|국내산)(?!.*원산지\\s*표시)"
  message_ko: "원산지 허위 표기 금지 — 실제 확인 필요"
  law_reference: "농수산물 원산지 표시에 관한 법률 제5조"
  auto_fix_suggestion: "엄선된 식재료 사용 — 원산지는 매장 내 표시 확인"
  tags: [origin, false_claim]

- id: RST-002
  type: must_exclude
  severity: warning
  pattern: "최고의?\\s*(맛|음식|식당)|맛집\\s*(1위|넘버원)|업계\\s*최고"
  message_ko: "최상급 맛 표현 금지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "정성을 담은 요리|전문 셰프의 자신작"
  tags: [superlative]

- id: RST-003
  type: must_exclude
  severity: critical
  pattern: "건강에\\s*(좋|효과)|질병\\s*(예방|치료)|면역력\\s*(강화|증진|향상)"
  message_ko: "음식에 대한 건강기능식품/의약품적 효능 표현 금지"
  law_reference: "식품표시광고법 제8조"
  auto_fix_suggestion: "신선한 재료로 정성껏 준비한"
  tags: [health_claim]

- id: RST-004
  type: must_exclude
  severity: warning
  pattern: "미쉐린|미슐랭|블루리본(?!.*실제\\s*선정)"
  message_ko: "실제 선정되지 않은 외부 평가 인용 금지"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "고객에게 사랑받는 맛"
  tags: [credential, false_claim]

- id: RST-005
  type: must_include
  severity: info
  required_text: "가격|메뉴|매장"
  trigger_when: contains_promotion
  message_ko: "이벤트/프로모션 시 가격 및 조건 확인 경로 안내 필요"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "자세한 메뉴와 가격은 매장에서 확인하세요"
  tags: [promotion, disclaimer]

- id: RST-006
  type: must_exclude
  severity: warning
  pattern: "타\\s*(음식점|식당|매장)(보다|에\\s*비해)"
  message_ko: "경쟁 업소 비교 표현 금지"
  law_reference: "표시광고법 제3조 제1항 제3호"
  auto_fix_suggestion: "표현 삭제"
  tags: [comparison]

- id: RST-007
  type: must_exclude
  severity: warning
  pattern: "무한\\s*리필.*무조건|공짜|0원\\s*(식사|음식)"
  message_ko: "조건 없는 무료 음식 표현은 기만 광고 소지"
  law_reference: "표시광고법 제3조 제1항 제2호"
  auto_fix_suggestion: "합리적인 가격의 푸짐한 한 끼"
  tags: [price, inducement]
```

### 3.5 fitness (피트니스) — 7개

```yaml
meta:
  vertical: fitness
  sub_vertical: default
  version: "1.0.0"
  description_ko: "피트니스/헬스/PT 광고 컴플라이언스 팩"

rules:
- id: FIT-001
  type: must_exclude
  severity: critical
  pattern: "\\d+kg\\s*(감량|빼기)\\s*(보장|확실|100%)|반드시\\s*\\d+kg"
  message_ko: "체중 감량 보장 표현 금지"
  law_reference: "표시광고법 제3조 (거짓 광고)"
  auto_fix_suggestion: "체계적인 운동 프로그램으로 건강한 체중 관리"
  tags: [guarantee, weight]

- id: FIT-002
  type: must_exclude
  severity: warning
  pattern: "전후\\s*(비교|사진)|비포(\\s*앤?\\s*)애프터|\\d+개월\\s*(전|후)\\s*(사진|모습)"
  message_ko: "전후 비교 사진/영상은 오인 유발 소지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "꾸준한 운동으로 건강한 변화를 만들어 보세요"
  tags: [before_after]

- id: FIT-003
  type: must_exclude
  severity: warning
  pattern: "최고의?\\s*(트레이너|PT|헬스장)|업계\\s*(1위|최고)"
  message_ko: "최상급 표현 금지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "전문 자격을 갖춘 트레이너"
  tags: [superlative]

- id: FIT-004
  type: must_exclude
  severity: critical
  pattern: "치료|재활\\s*(치료|프로그램)|의학적|처방"
  message_ko: "의료 행위(치료/재활치료) 표현은 비의료시설에서 금지"
  law_reference: "의료법 제27조"
  auto_fix_suggestion: "체계적인 운동 프로그램|기능 개선 트레이닝"
  tags: [medical_claim]

- id: FIT-005
  type: must_exclude
  severity: warning
  pattern: "\\d+일\\s*만에|\\d+주\\s*만에.*변화|빠른\\s*(효과|변화|결과)"
  message_ko: "단기간 효과 보장 표현 자제"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "개인의 노력과 체질에 따라 결과가 달라질 수 있습니다"
  tags: [timeline, guarantee]

- id: FIT-006
  type: must_include
  severity: info
  required_text: "개인(에 따라|차가|마다)"
  trigger_when: contains_effect
  message_ko: "운동 효과 언급 시 개인차 고지 권장"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "운동 효과는 개인에 따라 차이가 있을 수 있습니다"
  tags: [disclaimer]

- id: FIT-007
  type: must_exclude
  severity: warning
  pattern: "보충제|단백질\\s*보충.*효과|스테로이드|약물"
  message_ko: "건강기능식품/약물 관련 표현은 별도 규정 준수 필요"
  law_reference: "건강기능식품법 제18조"
  auto_fix_suggestion: "균형 잡힌 식단과 운동으로 건강하게"
  tags: [supplement, health_claim]
```

### 3.6 realestate (부동산) — 8개

```yaml
meta:
  vertical: realestate
  sub_vertical: default
  version: "1.0.0"
  description_ko: "부동산 중개/분양 광고 컴플라이언스 팩"

rules:
- id: RES-001
  type: must_exclude
  severity: critical
  pattern: "\\d+%\\s*(수익률|투자.*수익)|확정\\s*(수익|이자)|원금\\s*(보장|보전)"
  message_ko: "확정 수익률/원금 보장 표현 금지"
  law_reference: "공인중개사법 제18조의2, 부동산투자 광고 가이드라인"
  auto_fix_suggestion: "투자 수익은 시장 상황에 따라 변동될 수 있습니다"
  tags: [guarantee, investment]

- id: RES-002
  type: must_exclude
  severity: critical
  pattern: "시세\\s*(상승|폭등|급등)\\s*(확실|보장|예상)|오를\\s*수밖에|절대.*떨어지지"
  message_ko: "시세 상승 보장/단언 표현 금지"
  law_reference: "표시광고법 제3조, 부동산 거래신고 등에 관한 법률"
  auto_fix_suggestion: "부동산 시장은 다양한 요인에 영향을 받습니다"
  tags: [guarantee, price_prediction]

- id: RES-003
  type: must_exclude
  severity: warning
  pattern: "로또|대박|떼돈|한방에|투기|갭투자"
  message_ko: "투기 조장 표현 금지"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "표현 삭제"
  tags: [speculation]

- id: RES-004
  type: must_include
  severity: critical
  required_text: "중개\\s*보수|수수료|비용"
  trigger_when: always
  message_ko: "부동산 거래 관련 광고 시 중개보수 관련 안내 경로 필수"
  law_reference: "공인중개사법 제32조"
  auto_fix_suggestion: "중개보수 및 실비는 법정 기준에 따릅니다. 자세한 사항은 문의하세요."
  tags: [fee, disclaimer]

- id: RES-005
  type: must_exclude
  severity: warning
  pattern: "학군\\s*(최고|1등)|명문\\s*학군|\\d+대\\s*합격률\\s*\\d+%"
  message_ko: "학군 관련 과장 표현 자제"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "우수한 교육 환경을 갖춘 지역"
  tags: [exaggeration, school_district]

- id: RES-006
  type: must_exclude
  severity: critical
  pattern: "미등록\\s*중개|직거래\\s*전문|수수료\\s*없이\\s*거래"
  message_ko: "무등록 중개 암시 표현 금지"
  law_reference: "공인중개사법 제9조"
  auto_fix_suggestion: "공인중개사가 안전하게 거래를 도와드립니다"
  tags: [unlicensed, fee]

- id: RES-007
  type: must_exclude
  severity: warning
  pattern: "조망\\s*(확정|보장|영구)|영구\\s*조망|뷰\\s*(보장|확정)"
  message_ko: "조망 보장 표현 금지 — 주변 개발에 따라 변동 가능"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "현재 탁 트인 조망을 갖추고 있습니다 (주변 환경 변동 가능)"
  tags: [guarantee, view]

- id: RES-008
  type: llm_semantic
  severity: warning
  prompt_ko: |
    다음 부동산 광고 스크립트에서 실제 분양/매매 조건과 다르게 
    오해를 유발할 수 있는 표현이 있는지 판단하세요.
    특히 면적, 층수, 방향, 입주 시기 등에 대한 불명확한 표현에 주의하세요.
  examples:
    - input: "전 세대 남향 배치로 채광 걱정 없습니다"
      violation: true
      reason: "'전 세대 남향'은 검증 필요 — 일부 세대는 남동/남서일 수 있음"
    - input: "남향 위주의 세대 배치로 채광을 고려한 설계입니다"
      violation: false
      reason: "'남향 위주'로 완화, 전체 보장이 아님"
  message_ko: "분양/매매 조건에 대한 불명확/과장 표현 주의"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "정확한 세대 정보는 분양 사무실에서 확인하세요"
  tags: [specification, false_claim]
```

### 3.7 general (일반 업종) — 5개

```yaml
meta:
  vertical: general
  sub_vertical: default
  version: "1.0.0"
  description_ko: "범용 광고 컴플라이언스 팩 — 모든 vertical의 기본 베이스"

rules:
- id: GEN-001
  type: must_exclude
  severity: critical
  pattern: "최고의?|업계\\s*(1위|최초|넘버원)|국내\\s*(1위|최초)|세계\\s*(최초|1위)"
  message_ko: "객관적 근거 없는 최상급 표현 금지"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "검증된|전문적인|신뢰할 수 있는"
  tags: [superlative]

- id: GEN-002
  type: must_exclude
  severity: critical
  pattern: "100%\\s*(보장|확실|만족)|반드시|절대.*효과"
  message_ko: "효과/품질 보장 표현 금지"
  law_reference: "표시광고법 제3조 제1항 제1호"
  auto_fix_suggestion: "높은 만족도|꼼꼼한 서비스"
  tags: [guarantee]

- id: GEN-003
  type: must_exclude
  severity: warning
  pattern: "타\\s*(업체|업소|회사|매장)(보다|에\\s*비해|과\\s*비교|대비)"
  message_ko: "경쟁 업체 비교/비하 표현 금지"
  law_reference: "표시광고법 제3조 제1항 제3호"
  auto_fix_suggestion: "표현 삭제"
  tags: [comparison]

- id: GEN-004
  type: must_exclude
  severity: warning
  pattern: "허위|가짜(?!.*금지)|불법(?!.*아닌)"
  message_ko: "허위/불법 컨텐츠 암시 표현 주의"
  law_reference: "표시광고법 제3조"
  auto_fix_suggestion: "표현 삭제"
  tags: [illegal_content]

- id: GEN-005
  type: must_include
  severity: info
  required_text: "문의|상담|안내|전화|방문"
  trigger_when: always
  message_ko: "모든 광고에 문의/연락 경로 안내 권장"
  law_reference: "표시광고법 일반 가이드"
  auto_fix_suggestion: "자세한 내용은 문의해 주세요"
  tags: [contact, disclaimer]
```

---

## 4. 파이프라인 통합 설계

### 4.1 검증 파이프라인 위치

```
Writer Agent (스크립트 생성)
  ↓
┌─────────────────────────────────────────┐
│ ComplianceValidator (신규 서비스)         │
│                                         │
│  1. YAML 팩 로드                         │
│     load_pack(vertical, sub_vertical)    │
│                                         │
│  2. Static Rules 실행 (regex 기반)        │
│     - must_exclude → 패턴 매치 시 위반    │
│     - must_include → 패턴 미매치 시 위반   │
│     - trigger_when 조건 체크              │
│                                         │
│  3. Critical 위반 존재?                   │
│     ├─ Yes → Writer Agent에 auto_fix 전달 │
│     │        → 재생성 요청 (max 3회)       │
│     └─ No  → LLM Semantic Rules 실행     │
│                                         │
│  4. LLM Semantic Rules                   │
│     - Claude Haiku로 각 룰 prompt 실행    │
│     - few-shot examples 포함             │
│     - 위반 판정 시 결과 수집              │
│                                         │
│  5. ValidationReport 생성                │
│     - passed: bool                       │
│     - violations: list[Violation]        │
│     - warnings: list[Violation]          │
│     - auto_fixed: list[AutoFix]         │
│     - compliance_score: float (0~100)    │
└─────────────────────────────────────────┘
  ↓
  passed=true → TTS 생성 진행
  passed=false (critical 남음) → 수동 검토 대기 (FLAGGED 상태)
```

### 4.2 Auto-Fix 메커니즘

```
1. Static Rule 위반 감지
   예: MED-DERM-001 위반 — "최고의 피부과" 감지

2. auto_fix_suggestion 추출
   → "효과적인|검증된|전문적인"

3. Writer Agent에 재생성 프롬프트 전달:
   """
   아래 스크립트에서 광고법 위반 표현을 수정해주세요.
   
   [위반 목록]
   - MED-DERM-001: "최고의 피부과" → 최상급 표현 금지 (의료법 제56조)
     대체 표현 가이드: 효과적인 / 검증된 / 전문적인
   
   [원본 스크립트]
   {original_script}
   
   [규칙]
   - 위반 표현만 수정하고 나머지 스크립트는 그대로 유지
   - 자연스러운 문맥을 유지
   - 대체 표현 가이드를 참고하되 문맥에 맞게 변형 가능
   """

4. 재생성된 스크립트 → 다시 ComplianceValidator 통과
   → 최대 3회 반복 → 3회 초과 시 FLAGGED

5. LLM Semantic 위반은 auto_fix 불가
   → suggestion만 제공하고 FLAGGED 상태로 수동 검토 대기
```

### 4.3 서비스 구조

```
backend/
├── compliance_packs/                    # YAML 팩 디렉토리 (위 2~3절 내용)
│   ├── schema.yaml
│   ├── medical/dermatology.yaml
│   ├── academy/default.yaml
│   └── ...
│
├── app/services/
│   ├── compliance_validator.py          # 핵심 검증 엔진
│   │   ├── class ComplianceValidator
│   │   │   ├── load_pack(vertical, sub_vertical) → CompliancePack
│   │   │   ├── validate_static(script, pack) → list[Violation]
│   │   │   ├── validate_semantic(script, pack) → list[Violation]
│   │   │   ├── validate(script, vertical, sub_vertical) → ValidationReport
│   │   │   └── suggest_fix(script, violations) → str (재생성 프롬프트)
│   │   │
│   │   ├── class Violation
│   │   │   ├── rule_id: str
│   │   │   ├── severity: str
│   │   │   ├── matched_text: str
│   │   │   ├── message_ko: str
│   │   │   ├── law_reference: str
│   │   │   └── auto_fix_suggestion: str
│   │   │
│   │   └── class ValidationReport
│   │       ├── passed: bool
│   │       ├── violations: list[Violation]
│   │       ├── warnings: list[Violation]
│   │       ├── compliance_score: float
│   │       └── timestamp: datetime
│   │
│   └── writer_agent.py                 # 기존 — validate 단계 추가 필요
│       └── (스크립트 생성 후 ComplianceValidator.validate() 호출)
```

---

## 5. 비즈니스 규칙 목록

| ID | 규칙 | 비고 |
|----|------|------|
| BR-001 | 모든 스크립트는 해당 vertical의 compliance pack을 거쳐야 TTS로 진행 가능 | 파이프라인 게이트 |
| BR-002 | critical 위반이 1개라도 있으면 auto_fix 시도 → 3회 실패 시 FLAGGED 상태 | 자동 수정 한도 |
| BR-003 | warning은 리포트에 포함되지만 스크립트 진행을 차단하지 않음 | 유연성 확보 |
| BR-004 | info는 로깅만 — UI에 "권장 사항"으로 표시 | 정보성 |
| BR-005 | llm_semantic 룰은 static 룰 통과 후에만 실행 (비용 절감) | 비용 최적화 |
| BR-006 | compliance_score = max(0, 100 - (critical * 20 + warning * 5 + info * 1)). 음수 방지 필수. critical 5건 이상이면 무조건 0점. | 점수 산출 |
| BR-007 | 거래처(Client) 등록 시 vertical + sub_vertical 필수 입력 | 팩 자동 매칭 |
| BR-008 | 팩 버전 업데이트 시 기존 통과된 스크립트는 소급 검증하지 않음 | 운영 안정성 |
| BR-009 | general 팩은 모든 vertical의 기본 베이스로 항상 함께 적용 | 이중 레이어 |
| BR-010 | sub_vertical이 없는 vertical은 default.yaml 사용 | 폴백 |
| BR-011 | YAML 팩은 JSON Schema로 구조 검증 후에만 로드 가능 | 무결성 |
| BR-012 | 법령 개정 시 law_snapshot_date 업데이트 + 영향받는 룰 revision | 법령 추적 |

---

## 6. 검증 시나리오 목록

### 6.1 medical-dermatology 시나리오

| ID | 시나리오 | 입력 스크립트 (요약) | 기대 결과 |
|----|---------|---------------------|----------|
| SCN-001 | 최상급 표현 감지 | "국내 최고의 피부과에서 가장 좋은 시술을 받으세요" | MED-DERM-001 critical 위반 2건 |
| SCN-002 | 효과 보장 감지 | "이 시술을 받으면 100% 효과를 보장합니다" | MED-DERM-002 critical 위반 |
| SCN-003 | 비포애프터 LLM 감지 | "칙칙했던 피부가 시술 후 환하게 빛나게 됩니다" | MED-DERM-007 llm_semantic critical |
| SCN-004 | 가격 유인 감지 | "지금 등록하면 50% 할인! 선착순 10명 한정!" | MED-DERM-012 + MED-DERM-013 warning 2건 |
| SCN-005 | 고지 의무 누락 | "레이저 시술로 피부가 개선됩니다" (개인차 고지 없음) | MED-DERM-020 + MED-DERM-021 critical 2건 |
| SCN-006 | 복합 위반 | "명의가 최신 장비로 100% 효과 보장. 전후 사진 확인!" | MED-DERM-016+002+028+008 = 4건 위반 |
| SCN-007 | 정상 스크립트 통과 | "피부과 전문의가 개인 맞춤 상담을 통해 적합한 관리 방법을 안내합니다. 효과는 개인에 따라 다를 수 있으며 부작용이 있을 수 있으니 반드시 전문의와 상담하세요." | 위반 0건, passed=true |
| SCN-008 | auto_fix 성공 | "최고의 피부과" → auto_fix → "전문적인 피부과" | 1회 재생성으로 통과 |
| SCN-009 | auto_fix 3회 실패 | LLM이 계속 위반 표현 생성 | FLAGGED 상태 전환 |
| SCN-010 | 부작용 축소 LLM 감지 | "간단한 레이저라 걱정 없어요! 일상 복귀 바로 가능!" | MED-DERM-023 llm_semantic warning |

### 6.2 cross-vertical 시나리오

| ID | 시나리오 | vertical | 기대 결과 |
|----|---------|----------|----------|
| SCN-011 | 학원 합격 보장 | academy | ACD-001 critical |
| SCN-012 | 마트 최저가 주장 | mart | MRT-001 critical + GEN-001 critical (이중 레이어) |
| SCN-013 | 뷰티샵 의료 표현 | beauty | BTY-001 critical |
| SCN-014 | 음식점 건강 효능 | restaurant | RST-003 critical |
| SCN-015 | 피트니스 체중 보장 | fitness | FIT-001 critical |
| SCN-016 | 부동산 수익 보장 | realestate | RES-001 critical |
| SCN-017 | general 기본 필터 | general | GEN-001/002 기본 검사 |
| SCN-018 | vertical 미지정 시 | (없음) | general 팩으로 폴백 |
| SCN-019 | general + vertical 이중 검증 | academy | GEN-001~005 + ACD-001~010 모두 적용 |
| SCN-020 | 정상 스크립트 전 vertical | 각 vertical | 모든 vertical에서 passed=true 되는 모범 스크립트 세트 |

---

## 7. 법조항 참조 정리

| 법률 | 주요 조항 | 적용 vertical |
|------|----------|-------------|
| **의료법 제56조** | 의료광고 제한 (최상급/효과보장/비포애프터/허위자격/유인/비교/미승인기기) | medical |
| **의료법 시행규칙 제33조** | 부작용 고지 의무, 전문의 상담 권유 의무 | medical |
| **의료법 제27조** | 무면허 의료행위 금지 | beauty, fitness |
| **의료광고심의기준 제4조** | 비포앤애프터 사진/영상 제한 | medical |
| **표시광고법 제3조** | 거짓/과장/기만/부당비교 광고 금지 | **전 vertical** |
| **화장품법 제13조** | 화장품 과대광고 금지 | beauty |
| **식품표시광고법 제8조** | 식품 질병예방/치료 효능 표현 금지 | mart, restaurant |
| **농수산물 원산지 표시법 제5조** | 원산지 허위 표기 금지 | mart, restaurant |
| **친환경농어업법 제23조** | 무인증 유기농/무농약 표기 금지 | mart |
| **학원법 시행령 제18조** | 과도한 선행학습 조장 제한 | academy |
| **공인중개사법 제18조의2** | 부동산 허위/과장 광고 금지 | realestate |
| **공인중개사법 제32조** | 중개보수 고지 의무 | realestate |
| **건강기능식품법 제18조** | 건강기능식품 과대광고 금지 | fitness |
| **공정거래법 (전반)** | 부당 경쟁행위 금지 | **전 vertical** |

---

## 8. 우선순위 및 구현 로드맵 제안

| 순서 | 작업 | 의존성 |
|------|------|--------|
| 1 | `backend/compliance_packs/` 디렉토리 + `schema.yaml` 생성 | 없음 |
| 2 | `medical/dermatology.yaml` 작성 (30개 룰) | #1 |
| 3 | `general/default.yaml` 작성 (5개 룰) | #1 |
| 4 | `compliance_validator.py` — static rule 엔진 | #1 |
| 5 | 나머지 6개 vertical YAML 작성 | #1 |
| 6 | `compliance_validator.py` — llm_semantic 엔진 | #4 |
| 7 | Writer Agent 통합 (validate + auto_fix 루프) | #4, #6 |
| 8 | ValidationReport UI (프론트엔드) | #7 |
| 9 | 전체 시나리오 테스트 (SCN-001 ~ SCN-020) | #7 |

---

*끝. 이 문서는 ISS-039 DOMAIN_ANALYZE 산출물이며, 다음 단계에서 BIZ_VALIDATE + SCENARIO_PLAY로 검증됩니다.*
