# ULW (Ultra Work) 작업 전 필수 체크리스트

## 📋 대표님 지적사항
**문제**: "기획도 하고, 구현도 되어있고, 적용을 안해서 나한테 혼나고... 이런것을 반복하지 않으려면?"

**원인**:
1. 기존 구현을 제대로 파악하지 않음
2. 백엔드 API가 있는지 확인 안함
3. Phase 완료 리포트를 읽지 않음
4. 연결만 하면 되는데 처음부터 다시 구현하려 함

---

## ✅ ULW 시작 전 필수 단계

### 1. **Phase 완료 리포트 확인** (1순위)
```bash
# 작업 전 반드시 읽기
find . -name "*PHASE*REPORT*.md" -o -name "*COMPLETION*.md" -o -name "*IMPLEMENTATION*.md"
```

**확인 사항**:
- 해당 기능이 어느 Phase에서 완료되었는지
- 구현된 파일 경로
- API 엔드포인트
- 사용법

**예시**:
- Phase 3: Storyboard API 구현 완료 → `/api/v1/storyboard/campaigns/{id}/content/{id}/generate`
- Phase 3: Writer Agent 구현 완료 → `app/services/writer_agent.py`

---

### 2. **백엔드 API 존재 여부 확인** (2순위)
```bash
# API 라우트 검색
find backend/app/api -name "*.py" | xargs grep -l "router"

# 특정 기능 API 검색
grep -r "storyboard" backend/app/api/
grep -r "writer" backend/app/api/
```

**확인 사항**:
- 이미 구현된 API 엔드포인트
- Request/Response 모델
- 필수 파라미터

---

### 3. **서비스 레이어 확인** (3순위)
```bash
# 서비스 파일 검색
find backend/app/services -name "*.py"
find backend/app/agents -name "*.py"
```

**확인 사항**:
- 이미 구현된 Agent/Service
- 함수 시그니처
- 의존성

---

### 4. **프론트엔드 연동 상태 확인** (4순위)
```bash
# API 호출 검색
grep -r "fetch.*api" frontend/app/
grep -r "localhost:8020" frontend/
```

**확인 사항**:
- 어느 API가 연결되어 있는지
- 어느 API가 누락되었는지

---

## 🚨 금지 사항

### ❌ 하지 말아야 할 것

1. **바로 코드부터 작성**
   - Phase 리포트도 안 읽고 구현 시작
   - 이미 있는 API를 모르고 새로 만듦

2. **추측으로 작업**
   - "아마 이 API가 없을 거야" → 확인 안함
   - "이건 구현 안되어 있을 거야" → 검색 안함

3. **문서 무시**
   - REALPLAN.md 안 읽음
   - Phase 리포트 안 읽음
   - CLAUDE.md 안 읽음

---

## ✅ 올바른 ULW 워크플로우

### Step 1: **파악** (5분)
```bash
# 1. Phase 리포트 읽기
cat PHASE_*_COMPLETION_REPORT.md

# 2. 백엔드 API 검색
grep -r "함수명|키워드" backend/app/api/

# 3. 서비스 검색
grep -r "함수명|키워드" backend/app/services/
grep -r "함수명|키워드" backend/app/agents/

# 4. 프론트엔드 연동 검색
grep -r "fetch.*api" frontend/app/
```

### Step 2: **판단** (2분)
- 이미 구현되어 있는가? → **연결만 하면 됨**
- 부분적으로 구현되어 있는가? → **보완**
- 전혀 없는가? → **새로 구현**

### Step 3: **실행** (10분)
- **연결만 하면 되는 경우**: API 호출 코드만 추가
- **보완하는 경우**: 누락된 파라미터 추가
- **새로 구현하는 경우**: 설계 → 구현 → 테스트

---

## 📊 오늘 사례 분석

### 대표님 요청
> "콘티 블록은 훅/본문/CTA로 고정되어 있네. AI가 판단해서 내용을 나누자 했는데."

### 내가 한 실수
1. ❌ Phase 3 리포트를 읽지 않음
2. ❌ Storyboard API가 이미 있는지 확인 안함
3. ❌ Director Agent가 이미 동적 분할을 한다는 것을 모름
4. ❌ "구현해야겠다"라고 생각하고 바로 코딩 시작

### 올바른 접근
1. ✅ `PHASE_3_COMPLETION_REPORT.md` 읽기
2. ✅ `backend/app/api/v1/storyboard.py` 확인
3. ✅ `backend/app/agents/director_agent.py` 확인
4. ✅ "아, 이미 있네. 프론트엔드에서 호출만 하면 되겠다"
5. ✅ `frontend/app/studio/page.tsx`에 API 호출 코드 추가 (5분 완료)

**시간 차이**:
- 내가 한 방식: 30분 (삽질 + 혼남)
- 올바른 방식: 10분 (파악 5분 + 연결 5분)

---

## 🎯 앞으로의 원칙

### 1. **"구현"보다 "연결"을 먼저 생각**
   - 이미 있는 기능을 찾아서 연결
   - 없으면 그때 구현

### 2. **문서를 신뢰**
   - Phase 리포트가 있으면 99% 구현되어 있음
   - REALPLAN.md에 있으면 100% 기획되어 있음

### 3. **검색을 생활화**
   - `grep -r "키워드" backend/`
   - `find . -name "*키워드*.py"`

### 4. **대표님께 확인**
   - "이 기능이 이미 구현되어 있습니까?"
   - "어느 Phase에서 완료되었습니까?"

---

## 📝 ULW 작업 전 자동 체크 스크립트

```bash
#!/bin/bash
# ulw-check.sh - ULW 작업 전 자동 체크

echo "🔍 ULW 작업 전 체크리스트"
echo ""

echo "1. Phase 리포트 확인"
find . -name "*PHASE*REPORT*.md" -o -name "*COMPLETION*.md" | head -10
echo ""

echo "2. 백엔드 API 목록"
find backend/app/api -name "*.py" -type f | xargs grep -l "@router" | head -10
echo ""

echo "3. 서비스/Agent 목록"
find backend/app/services backend/app/agents -name "*.py" -type f 2>/dev/null | head -10
echo ""

echo "4. 프론트엔드 API 호출"
grep -r "fetch.*api" frontend/app/ 2>/dev/null | cut -d: -f1 | sort -u | head -10
echo ""

echo "✅ 체크 완료. 이제 작업 시작하세요."
```

**사용법**:
```bash
chmod +x ulw-check.sh
./ulw-check.sh
```

---

## 🎓 학습 포인트

### 대표님의 핵심 지적
> "기획도 하고, 구현도 되어있고, 적용을 안해서..."

**교훈**:
1. **기획 확인**: REALPLAN.md, Phase 문서
2. **구현 확인**: 백엔드 API, 서비스, Agent
3. **적용 확인**: 프론트엔드 연동
4. **누락된 연결고리 찾기**: 3개 중 어디가 빠졌는지

---

## 🚀 다음부터는

```
대표님 요청
  ↓
Phase 리포트 확인 (5분)
  ↓
백엔드 API 확인 (2분)
  ↓
프론트엔드 연동 확인 (2분)
  ↓
[이미 있음] → 연결만 (5분)
[부분 구현] → 보완 (10분)
[전혀 없음] → 새로 구현 (30분+)
```

**총 소요 시간**: 10~50분 (삽질 0분)

---

## 🧪 테스트 실수 방지 (2026-02-02 추가)

### 대표님 지적
> "테스트 할때 이런걸 못 찾아내나? 그게 테스트야!"

### 내가 한 실수 (Writer Agent 케이스)

**문제 상황**:
- 프론트엔드에서 스크립트가 placeholder로만 생성됨
- "주제: 저시력인 이번에 대한 상세한 설명과 정보"

**내가 한 것** (잘못된 순서):
1. ❌ `/api/writer-generate/route.ts` 읽기
2. ❌ Mock 데이터 발견
3. ❌ 백엔드 API로 연결 시도
4. ❌ curl 테스트 → 404 에러
5. ✅ 문제 발견: Writer Agent 라우터가 비활성화됨

**해야 했던 것** (올바른 순서):
1. ✅ **Phase 리포트 확인** → Writer Agent 구현 상태 파악
2. ✅ **백엔드 라우터 등록 확인** → `/api/v1/__init__.py` 체크
3. ✅ **curl 테스트** → 404 에러로 문제 조기 발견
4. ✅ **원인 분석** → 라우터 비활성화 확인
5. ✅ **해결 방안 제시** → Option A/B/C 제시

---

### ✅ 테스트 전 필수 체크 (3단계)

#### 1단계: 라우터 등록 여부 확인 (1분)
```bash
# 백엔드 라우터 확인
grep -n "writer" backend/app/api/v1/__init__.py

# 주석 처리되어 있는지 확인
grep -n "# from .writer" backend/app/api/v1/__init__.py
```

**판단**:
- 주석 처리(`#`)되어 있으면 → **비활성화됨**
- `router.include_router(writer_router)`가 없으면 → **등록 안됨**

#### 2단계: 엔드포인트 테스트 (1분)
```bash
# 간단한 GET 테스트
curl -s http://localhost:8000/api/v1/writer/health

# POST 테스트 (실제 요청)
curl -s -X POST http://localhost:8000/api/v1/writer/generate \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_id":"test","campaign_name":"테스트","topic":"AI","platform":"Youtube"}'
```

**예상 결과**:
- `{"detail":"Not Found"}` → **라우터 미등록**
- `{"success":false,"error":"..."}` → **API는 등록되었지만 에러**
- `{"success":true,...}` → **정상 작동**

#### 3단계: 프론트엔드 연동 확인 (1분)
```bash
# 프론트엔드가 어디로 호출하는지 확인
grep -n "writer" frontend/app/api/writer-generate/route.ts

# 백엔드 URL 확인
grep -n "localhost:8000" frontend/app/api/writer-generate/route.ts
```

---

### 🚨 테스트 실수 패턴

#### 실수 1: 구현만 보고 테스트 안함
```
코드 읽기 → "구현되어 있네!" → 끝
                              ↑
                         [테스트 누락]
```

**올바른 방식**:
```
코드 읽기 → 구현 확인 → curl 테스트 → 결과 확인
```

#### 실수 2: 에러를 늦게 발견
```
프론트엔드 구현 → 백엔드 연결 → 실행 → 에러!
                                      ↑
                              [너무 늦게 발견]
```

**올바른 방식**:
```
백엔드 테스트 → 에러 발견 → 수정 → 프론트엔드 연결
      ↑
  [조기 발견]
```

#### 실수 3: 라우터 등록을 확인 안함
```
API 파일 존재 → "구현되어 있다!" → 연결 시도 → 404 에러
                              ↑
                    [라우터 등록 확인 안함]
```

**올바른 방식**:
```
API 파일 존재 → __init__.py 확인 → 라우터 등록 확인 → 테스트
```

---

### 📋 테스트 체크리스트

구현 전:
- [ ] Phase 리포트 읽었는가?
- [ ] 백엔드 API 파일이 존재하는가?
- [ ] `__init__.py`에 라우터가 등록되어 있는가?
- [ ] 라우터가 주석 처리되어 있지 않은가?

테스트 중:
- [ ] curl로 엔드포인트 테스트했는가?
- [ ] 404 에러가 발생하지 않는가?
- [ ] Response가 예상과 일치하는가?

구현 후:
- [ ] 프론트엔드 연동이 정상 작동하는가?
- [ ] E2E 테스트를 실행했는가?
- [ ] 에러 처리가 되어 있는가?

---

### 🎯 테스트 자동화 스크립트

```bash
#!/bin/bash
# test-api.sh - API 테스트 자동화

BACKEND_URL="http://localhost:8000"
API_PATH="/api/v1/writer"

echo "🧪 API 테스트 시작"
echo ""

# 1. 라우터 등록 확인
echo "1. 라우터 등록 확인"
if grep -q "# from .writer" backend/app/api/v1/__init__.py; then
  echo "❌ Writer 라우터가 주석 처리되어 있습니다"
  exit 1
elif grep -q "from .writer" backend/app/api/v1/__init__.py; then
  echo "✅ Writer 라우터가 등록되어 있습니다"
else
  echo "❌ Writer 라우터가 등록되지 않았습니다"
  exit 1
fi
echo ""

# 2. Health 체크
echo "2. Health 엔드포인트 테스트"
RESPONSE=$(curl -s "$BACKEND_URL$API_PATH/health")
if echo "$RESPONSE" | grep -q "healthy"; then
  echo "✅ Health 체크 성공"
else
  echo "❌ Health 체크 실패: $RESPONSE"
fi
echo ""

# 3. Generate 엔드포인트 테스트
echo "3. Generate 엔드포인트 테스트"
RESPONSE=$(curl -s -X POST "$BACKEND_URL$API_PATH/generate" \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_id":"test","campaign_name":"테스트","topic":"AI","platform":"Youtube"}')

if echo "$RESPONSE" | grep -q "Not Found"; then
  echo "❌ 404 에러 - 라우터 미등록"
  exit 1
elif echo "$RESPONSE" | grep -q "success"; then
  echo "✅ API 호출 성공"
else
  echo "⚠️  에러 발생: $RESPONSE"
fi
echo ""

echo "🎉 테스트 완료"
```

**사용법**:
```bash
chmod +x test-api.sh
./test-api.sh
```

---

### 🎓 핵심 교훈

**대표님 말씀**:
> "테스트 할때 이런걸 못 찾아내나? 그게 테스트야!"

**교훈**:
1. **구현 확인 ≠ 작동 확인**
   - 코드가 있다고 작동하는게 아님
   - 반드시 curl로 테스트

2. **라우터 등록은 필수**
   - API 파일만 있어도 소용 없음
   - `__init__.py`에 등록되어야 작동

3. **조기 테스트**
   - 프론트엔드 연결 전에 백엔드부터 테스트
   - 에러는 빨리 발견할수록 좋음

4. **자동화**
   - 반복되는 테스트는 스크립트로
   - 실수를 줄이는 가장 확실한 방법

---

**작성일**: 2026-02-02
**작성 계기**: 대표님 피드백 - "반복하지 않으려면 어떻게 해야하나?" / "테스트 할때 이런걸 못 찾아내나?"
**핵심**: **파악 → 판단 → 실행 → 테스트** (구현보다 연결을 먼저, 연결 전에 테스트를 먼저!)
