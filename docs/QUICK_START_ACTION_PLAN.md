# ⚡ Quick Start Action Plan - OmniVibe Pro

> **2주 집중 실행 계획 (Remotion 통합 버전)**
> **Period**: 2026-02-08 ~ 2026-02-21 (14일)
> **Goal**: MVP 95% 완성 + Production 배포 준비

---

## 🎯 Week 1: Remotion 통합 및 Core Features

### Day 1 (2026-02-08) - Neo4j GraphRAG 시작

#### Morning (3시간)
**Task**: Neo4j 설치 및 설정

```bash
# Neo4j Docker 실행
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/omnivibe2026 \
  -v $(pwd)/neo4j_data:/data \
  neo4j:5.16

# 접속 확인
# Browser: http://localhost:7474
# ID: neo4j / PW: omnivibe2026
```

**Task**: Script Node 스키마 설계

```cypher
-- Neo4j Browser에서 실행

-- Script Node 생성
CREATE (s:Script {
  id: "script_001",
  content: "여러분, 오늘은 AI 비디오 에디터를 소개합니다...",
  platform: "YouTube",
  tone: "professional",
  gender: "male",
  word_count: 250,
  performance_score: 8.5,
  created_at: datetime()
})

-- Campaign Node 생성
CREATE (c:Campaign {
  id: "campaign_001",
  name: "신제품 런칭",
  industry: "tech"
})

-- 관계 설정
MATCH (s:Script {id: "script_001"})
MATCH (c:Campaign {id: "campaign_001"})
CREATE (s)-[:BELONGS_TO]->(c)
```

#### Afternoon (4시간)
**Task**: Writer Agent에 Neo4j Memory 통합

```python
# backend/app/services/neo4j_client.py
from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def search_similar_scripts(
        self, platform: str, tone: str, limit: int = 3
    ) -> list:
        """유사한 스타일의 고성과 스크립트 검색"""

        query = """
        MATCH (s:Script)
        WHERE s.platform = $platform
          AND s.tone = $tone
          AND s.performance_score > 8.0
        ORDER BY s.performance_score DESC
        LIMIT $limit
        RETURN s.content AS content, s.performance_score AS score
        """

        with self.driver.session() as session:
            result = session.run(query, platform=platform, tone=tone, limit=limit)
            return [{"content": record["content"], "score": record["score"]}
                    for record in result]

    def save_script(self, script_data: dict):
        """새 스크립트를 Neo4j에 저장"""

        query = """
        CREATE (s:Script {
          id: $id,
          content: $content,
          platform: $platform,
          tone: $tone,
          word_count: $word_count,
          created_at: datetime()
        })
        """

        with self.driver.session() as session:
            session.run(query, **script_data)
```

**Task**: Writer Agent 수정

```python
# backend/app/services/writer_agent.py (수정)
from app.services.neo4j_client import Neo4jClient

def search_similar_scripts(state: WriterState) -> WriterState:
    """Neo4j에서 유사한 스크립트 검색"""

    neo4j = Neo4jClient(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="omnivibe2026"
    )

    similar = neo4j.search_similar_scripts(
        platform=state["platform"],
        tone=state["tone"],
        limit=3
    )

    state["similar_scripts"] = similar
    return state
```

**Deliverable**:
- [ ] Neo4j 설치 완료
- [ ] 샘플 스크립트 10개 저장
- [ ] Writer Agent에서 검색 동작 확인

---

### Day 2 (2026-02-09) - Neo4j 완성 및 테스트

#### Morning (3시간)
**Task**: Neo4j 샘플 데이터 대량 삽입

```python
# scripts/seed_neo4j.py
from app.services.neo4j_client import Neo4jClient

neo4j = Neo4jClient(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="omnivibe2026"
)

sample_scripts = [
    {
        "id": "script_001",
        "content": "여러분, 오늘은 AI 비디오 에디터를 소개합니다...",
        "platform": "YouTube",
        "tone": "professional",
        "word_count": 250
    },
    # ... 총 10개
]

for script in sample_scripts:
    neo4j.save_script(script)

print("✅ 10 sample scripts inserted!")
```

#### Afternoon (4시간)
**Task**: E2E 테스트

```python
# tests/integration/test_writer_agent_memory.py
import pytest
from app.services.writer_agent import create_writer_graph

@pytest.mark.asyncio
async def test_writer_with_memory():
    graph = create_writer_graph()

    result = graph.invoke({
        "campaign_name": "Test Campaign",
        "topic": "AI 테스트",
        "platform": "YouTube",
        "tone": "professional"
    })

    assert result["similar_scripts"] is not None
    assert len(result["similar_scripts"]) > 0
    assert result["script"] is not None
```

**Deliverable**:
- [ ] 통합 테스트 통과
- [ ] 일관성 점수 측정 (수동 평가)

---

### Day 3 (2026-02-10) - Remotion Player 통합 🎬

#### Morning (3시간)
**Task**: Studio UI 기본 레이아웃 생성

```tsx
// frontend/app/studio/page.tsx
'use client';

import { useState } from 'react';
import { Player } from '@remotion/player';
import { YouTubeTemplate } from '@/remotion/templates/YouTubeTemplate';
import { Card } from '@/components/slds/layout/Card';
import { Button } from '@/components/slds/base/Button';

export default function StudioPage() {
  const [remotionProps, setRemotionProps] = useState({
    blocks: [
      {
        type: 'hook',
        text: '여러분, 오늘은 놀라운 AI 비디오 에디터를 소개합니다!',
        startTime: 0,
        duration: 5,
        backgroundUrl: 'https://source.unsplash.com/1920x1080/?technology',
        fontSize: 56
      },
      {
        type: 'body',
        text: '이 에디터는 스크립트만 입력하면 자동으로 영상을 만들어줍니다.',
        startTime: 5,
        duration: 10,
        backgroundUrl: 'https://source.unsplash.com/1920x1080/?coding',
        fontSize: 48
      }
    ],
    audioUrl: '',
    branding: {
      logo: '',
      primaryColor: '#00A1E0'
    }
  });

  return (
    <div className="min-h-screen bg-slds-background p-slds-large">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-slds-text-heading mb-slds-large">
          OmniVibe Pro Studio
        </h1>

        <div className="grid grid-cols-2 gap-slds-large">
          {/* 좌측: Script Editor */}
          <Card title="Script Blocks" icon="📝">
            <div className="space-y-slds-small">
              {remotionProps.blocks.map((block, idx) => (
                <div
                  key={idx}
                  className="p-slds-medium bg-white rounded-lg border border-slds-border"
                >
                  <div className="flex items-center justify-between mb-slds-x-small">
                    <span className="text-sm font-semibold text-slds-brand">
                      {block.type.toUpperCase()}
                    </span>
                    <span className="text-xs text-slds-text-weak">
                      {block.duration}s
                    </span>
                  </div>
                  <textarea
                    className="w-full p-slds-small border border-slds-border rounded"
                    rows={2}
                    value={block.text}
                    onChange={(e) => {
                      const updated = [...remotionProps.blocks];
                      updated[idx].text = e.target.value;
                      setRemotionProps({ ...remotionProps, blocks: updated });
                    }}
                  />
                </div>
              ))}
            </div>

            <Button variant="brand" className="mt-slds-medium w-full">
              + Add Block
            </Button>
          </Card>

          {/* 우측: Real-time Preview */}
          <Card title="Preview" icon="🎬">
            <Player
              component={YouTubeTemplate}
              durationInFrames={450} // 15초 * 30fps
              compositionWidth={1920}
              compositionHeight={1080}
              fps={30}
              inputProps={remotionProps}
              controls
              style={{ width: '100%', borderRadius: '8px' }}
            />

            <div className="mt-slds-medium flex gap-slds-small">
              <Button variant="brand" className="flex-1">
                Generate Audio
              </Button>
              <Button variant="success" className="flex-1">
                Render Video
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
```

#### Afternoon (4시간)
**Task**: Director Agent Props → Remotion Props 변환 API

```python
# backend/app/api/v1/storyboard.py (추가)

@router.get("/api/v1/storyboard/campaigns/{campaign_id}/content/{content_id}/remotion-props")
async def get_remotion_props(
    campaign_id: int,
    content_id: int,
    db: Session = Depends(get_db)
):
    """Director Agent의 Storyboard를 Remotion Props로 변환"""

    content = db.query(Content).filter_by(id=content_id).first()
    blocks = db.query(ScriptBlock).filter_by(content_id=content_id).all()

    remotion_blocks = [
        {
            "type": block.block_type,
            "text": block.text,
            "startTime": block.start_time,
            "duration": block.duration,
            "backgroundUrl": block.background_url,
            "fontSize": 56 if block.block_type == "hook" else 48
        }
        for block in blocks
    ]

    return {
        "blocks": remotion_blocks,
        "audioUrl": content.audio_url or "",
        "branding": {
            "logo": "",
            "primaryColor": "#00A1E0"
        }
    }
```

**Deliverable**:
- [ ] Studio UI에서 실시간 Preview 동작
- [ ] 블록 수정 시 자동 반영

---

### Day 4-5 (2026-02-11~12) - Backend Remotion Service 🔧

#### Day 4 Morning (3시간)
**Task**: Remotion Service 생성

```python
# backend/app/services/remotion_service.py
import subprocess
import json
import os
from app.tasks.celery_app import celery_app
from app.services.cloudinary_service import upload_video

@celery_app.task(bind=True)
def render_video_task(self, content_id: int, remotion_props: dict, platform: str = "youtube"):
    """Remotion으로 영상 렌더링"""

    try:
        # 1. Props를 JSON 파일로 저장
        props_file = f"/tmp/props_{content_id}.json"
        with open(props_file, 'w') as f:
            json.dump(remotion_props, f)

        # 2. Remotion 렌더링
        output_file = f"/tmp/video_{content_id}.mp4"

        cmd = [
            "npx", "remotion", "render",
            "remotion/Root.tsx",
            platform,  # "youtube" | "instagram" | "tiktok"
            output_file,
            f"--props={props_file}"
        ]

        # Progress update
        self.update_state(state="PROGRESS", meta={"stage": "rendering", "progress": 50})

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/app/frontend"  # Docker 경로
        )

        if result.returncode != 0:
            raise Exception(f"Remotion render failed: {result.stderr}")

        # 3. Cloudinary 업로드
        self.update_state(state="PROGRESS", meta={"stage": "uploading", "progress": 80})

        video_url = upload_video(output_file, folder="omnivibe/videos")

        # 4. DB 업데이트
        from app.db.sqlite_client import get_db
        db = next(get_db())
        content = db.query(Content).filter_by(id=content_id).first()
        content.video_url = video_url
        content.status = "video_rendered"
        db.commit()

        # 5. 임시 파일 삭제
        os.remove(props_file)
        os.remove(output_file)

        return {"video_url": video_url, "status": "completed"}

    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
```

#### Day 4 Afternoon (4시간)
**Task**: API Endpoint 생성

```python
# backend/app/api/v1/video.py
from fastapi import APIRouter, Depends
from app.services.remotion_service import render_video_task
from celery.result import AsyncResult

router = APIRouter()

@router.post("/api/v1/video/render")
async def render_video(request: VideoRenderRequest):
    """Remotion으로 영상 렌더링 (비동기)"""

    task = render_video_task.delay(
        content_id=request.content_id,
        remotion_props=request.remotion_props,
        platform=request.platform
    )

    return {
        "task_id": task.id,
        "status": "processing",
        "message": "Video rendering started. Use /video/status/{task_id} to check progress."
    }

@router.get("/api/v1/video/status/{task_id}")
async def get_video_status(task_id: str):
    """렌더링 상태 조회"""

    task = AsyncResult(task_id, app=celery_app)

    if task.state == "PENDING":
        return {"status": "pending"}
    elif task.state == "PROGRESS":
        return {
            "status": "processing",
            "stage": task.info.get("stage"),
            "progress": task.info.get("progress")
        }
    elif task.state == "SUCCESS":
        return {
            "status": "completed",
            "video_url": task.result["video_url"]
        }
    else:
        return {"status": "failed", "error": str(task.info)}
```

#### Day 5 (전체 7시간)
**Task**: E2E 테스트 및 최적화

```python
# tests/e2e/test_remotion_pipeline.py
import pytest
from httpx import AsyncClient
import asyncio

@pytest.mark.asyncio
async def test_full_remotion_pipeline(client: AsyncClient):
    # 1. Remotion Props 생성
    response = await client.get("/api/v1/storyboard/campaigns/1/content/1/remotion-props")
    assert response.status_code == 200
    remotion_props = response.json()

    # 2. 렌더링 시작
    response = await client.post("/api/v1/video/render", json={
        "content_id": 1,
        "remotion_props": remotion_props,
        "platform": "youtube"
    })
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # 3. 상태 폴링 (최대 3분)
    for _ in range(180):
        response = await client.get(f"/api/v1/video/status/{task_id}")
        status = response.json()["status"]

        if status == "completed":
            assert "video_url" in response.json()
            print(f"✅ Video rendered: {response.json()['video_url']}")
            break
        elif status == "failed":
            pytest.fail(f"Rendering failed: {response.json()['error']}")

        await asyncio.sleep(1)
```

**Deliverable**:
- [ ] API `/api/v1/video/render` 동작 확인
- [ ] 평균 렌더링 시간 < 2분
- [ ] Cloudinary URL 반환 성공

---

## 🎯 Week 2: Production 준비 및 Lambda 배포

### Day 6 (2026-02-13) - Script Block 드래그 앤 드롭

#### Full Day (7시간)
**Task**: DnD Kit 통합

```tsx
// frontend/components/ScriptBlockList.tsx
'use client';

import { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const SortableBlock = ({ block, index }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: block.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="p-slds-medium bg-white rounded-lg border border-slds-border mb-slds-small cursor-move"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slds-brand">
          {index + 1}. {block.type.toUpperCase()}
        </span>
        <span className="text-xs text-slds-text-weak">
          {block.duration}s
        </span>
      </div>
      <p className="mt-slds-x-small text-sm">{block.text}</p>
    </div>
  );
};

export const ScriptBlockList = ({ blocks, onReorder }) => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over.id) {
      const oldIndex = blocks.findIndex((b) => b.id === active.id);
      const newIndex = blocks.findIndex((b) => b.id === over.id);

      const reordered = arrayMove(blocks, oldIndex, newIndex);

      // start_time 재계산
      let currentTime = 0;
      const updated = reordered.map((block) => ({
        ...block,
        startTime: currentTime,
        endTime: (currentTime += block.duration)
      }));

      onReorder(updated);
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={blocks.map((b) => b.id)}
        strategy={verticalListSortingStrategy}
      >
        {blocks.map((block, idx) => (
          <SortableBlock key={block.id} block={block} index={idx} />
        ))}
      </SortableContext>
    </DndContext>
  );
};
```

**Deliverable**:
- [ ] 드래그 앤 드롭 부드럽게 동작
- [ ] 타이밍 자동 재계산

---

### Day 7-8 (2026-02-14~15) - Lambda 배포 ☁️

#### Day 7 Morning (3시간)
**Task**: AWS Lambda 함수 생성

```bash
# AWS CLI로 Lambda 함수 생성
cd frontend

# Remotion Lambda 사이트 생성
npx remotion lambda sites create remotion/Root.tsx \
  --site-name omnivibe-remotion

# Lambda 함수 배포
npx remotion lambda functions deploy \
  --region ap-northeast-2 \
  --memory 3009 \
  --disk 2048 \
  --timeout 900
```

#### Day 7 Afternoon (4시간)
**Task**: Backend Lambda 호출 로직

```python
# backend/app/services/remotion_lambda_service.py
import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-northeast-2')

@celery_app.task
def render_video_lambda(content_id: int, remotion_props: dict, platform: str):
    """AWS Lambda로 Remotion 렌더링"""

    payload = {
        "composition": platform,
        "serveUrl": "https://omnivibe-remotion.s3.amazonaws.com",
        "inputProps": remotion_props,
        "codec": "h264",
        "imageFormat": "jpeg"
    }

    response = lambda_client.invoke(
        FunctionName='remotion-render-function',
        InvocationType='Event',  # 비동기
        Payload=json.dumps(payload)
    )

    # S3에서 결과 폴링...
    return {"status": "rendering"}
```

#### Day 8 (전체 7시간)
**Task**: 테스트 및 비용 추적

```python
# tests/performance/test_lambda_rendering.py
import time
import pytest

def test_lambda_rendering_speed():
    start = time.time()

    # Lambda 렌더링 호출
    response = render_video_lambda(
        content_id=1,
        remotion_props={...},
        platform="youtube"
    )

    # 결과 대기
    # ...

    elapsed = time.time() - start

    # 30초 이내에 완료되어야 함
    assert elapsed < 30, f"Rendering took {elapsed}s (expected < 30s)"
```

**Deliverable**:
- [ ] Lambda 렌더링 < 30초
- [ ] 비용 < $0.05/video
- [ ] Logfire로 비용 추적

---

### Day 9-14 (2026-02-16~21) - Testing & Polish

- **Day 9-10**: 통합 테스트 (E2E)
- **Day 11-12**: 성능 최적화
- **Day 13**: UI/UX 폴리싱
- **Day 14**: 최종 데모 준비

---

## ✅ Success Criteria

### Technical KPIs
- [ ] Neo4j에 100개+ 스크립트 저장
- [ ] Writer Agent 일관성 > 85%
- [ ] 렌더링 시간 < 2분 (로컬) / < 30초 (Lambda)
- [ ] Audio 정확도 > 99%
- [ ] Lighthouse Score > 90

### Business KPIs
- [ ] 데모 영상 10개 생성
- [ ] A/B 테스트 결과 CTR +20%
- [ ] 개발 속도 3배 향상 (사용자 피드백)

---

**문서 버전**: 2.0 (Remotion 통합)
**작성일**: 2026-02-08
**상태**: ✅ Ready to Start!
