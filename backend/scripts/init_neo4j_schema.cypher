// Neo4j Schema Initialization for OmniVibe Pro
// GraphRAG Memory for Writer Agent

// ==================== Node Constraints ====================

// Script Node - Unique ID constraint
CREATE CONSTRAINT script_id_unique IF NOT EXISTS
FOR (s:Script) REQUIRE s.id IS UNIQUE;

// Campaign Node - Unique ID constraint
CREATE CONSTRAINT campaign_id_unique IF NOT EXISTS
FOR (c:Campaign) REQUIRE c.id IS UNIQUE;

// ==================== Indexes ====================

// Script 검색 최적화
CREATE INDEX script_platform IF NOT EXISTS
FOR (s:Script) ON (s.platform);

CREATE INDEX script_tone IF NOT EXISTS
FOR (s:Script) ON (s.tone);

CREATE INDEX script_performance IF NOT EXISTS
FOR (s:Script) ON (s.performance_score);

// Campaign 검색 최적화
CREATE INDEX campaign_industry IF NOT EXISTS
FOR (c:Campaign) ON (c.industry);

// ==================== Sample Data ====================

// Campaign Nodes
CREATE (c1:Campaign {
  id: "campaign_001",
  name: "신제품 런칭 캠페인",
  industry: "tech",
  target_audience: "MZ세대",
  created_at: datetime()
});

CREATE (c2:Campaign {
  id: "campaign_002",
  name: "브랜드 인지도 향상",
  industry: "fashion",
  target_audience: "2030 여성",
  created_at: datetime()
});

CREATE (c3:Campaign {
  id: "campaign_003",
  name: "교육 콘텐츠 시리즈",
  industry: "education",
  target_audience: "직장인",
  created_at: datetime()
});

// Script Nodes - High Performance Examples
CREATE (s1:Script {
  id: "script_001",
  content: "여러분, 오늘은 놀라운 AI 비디오 에디터를 소개합니다! 이 툴 하나면 전문가 수준의 영상을 단 5분 만에 완성할 수 있죠. 복잡한 편집 프로그램은 이제 안녕! 스크립트만 입력하면 AI가 알아서 멋진 영상을 만들어줍니다. 지금 바로 시작해보세요!",
  platform: "YouTube",
  tone: "energetic",
  gender: "male",
  word_count: 120,
  performance_score: 9.2,
  views: 150000,
  ctr: 0.12,
  created_at: datetime()
});

CREATE (s2:Script {
  id: "script_002",
  content: "안녕하세요, 오늘은 마케팅 자동화에 대해 알아보겠습니다. 많은 기업들이 반복적인 작업에 시간을 낭비하고 있습니다. 하지만 AI를 활용하면 이 모든 과정을 자동화할 수 있죠. 캠페인 기획부터 콘텐츠 제작, 배포까지 원클릭으로 해결하세요.",
  platform: "YouTube",
  tone: "professional",
  gender: "female",
  word_count: 110,
  performance_score: 8.7,
  views: 85000,
  ctr: 0.09,
  created_at: datetime()
});

CREATE (s3:Script {
  id: "script_003",
  content: "저시력은 일반적인 시력 기준인 20/20보다 상당히 낮은 수준입니다. 주요 원인으로는 노화성 황반변성, 당뇨병성 망막병증, 녹내장 등이 있죠. 조기 발견과 치료가 중요합니다. 정기적인 안과 검진으로 눈 건강을 지키세요.",
  platform: "YouTube",
  tone: "educational",
  gender: "neutral",
  word_count: 95,
  performance_score: 8.5,
  views: 120000,
  ctr: 0.10,
  created_at: datetime()
});

CREATE (s4:Script {
  id: "script_004",
  content: "오늘의 팁! 생산성을 높이는 3가지 비법을 공개합니다. 첫째, 아침 루틴을 확립하세요. 둘째, 집중 시간을 블록으로 나누세요. 셋째, 불필요한 회의는 과감히 거절하세요. 이 세 가지만 실천해도 업무 효율이 2배 향상됩니다!",
  platform: "Instagram",
  tone: "casual",
  gender: "female",
  word_count: 85,
  performance_score: 9.0,
  views: 200000,
  ctr: 0.15,
  created_at: datetime()
});

CREATE (s5:Script {
  id: "script_005",
  content: "놀라운 사실! AI가 이제 영상까지 만들어줍니다. 텍스트만 입력하면 자동으로 씬을 나누고, 배경을 추천하고, 음성까지 생성해주죠. 더 이상 값비싼 제작 비용은 필요 없어요. 누구나 크리에이터가 될 수 있는 시대입니다!",
  platform: "TikTok",
  tone: "playful",
  gender: "male",
  word_count: 90,
  performance_score: 9.5,
  views: 500000,
  ctr: 0.18,
  created_at: datetime()
});

CREATE (s6:Script {
  id: "script_006",
  content: "프로페셔널 마케터가 되는 방법을 알려드립니다. 데이터 분석 능력, 창의적 사고, 그리고 AI 툴 활용 능력이 핵심입니다. 특히 요즘은 AI를 얼마나 잘 활용하느냐가 경쟁력을 좌우하죠. OmniVibe Pro로 시작해보세요.",
  platform: "YouTube",
  tone: "professional",
  gender: "male",
  word_count: 100,
  performance_score: 8.8,
  views: 95000,
  ctr: 0.11,
  created_at: datetime()
});

CREATE (s7:Script {
  id: "script_007",
  content: "여러분의 브랜드 스토리를 영상으로 만들어보세요. 감동적인 이야기는 사람들의 마음을 움직입니다. AI가 당신의 메시지를 시각화하고, 최적의 타이밍에 배포까지 해드립니다. 브랜드 가치를 높이는 가장 쉬운 방법입니다.",
  platform: "Instagram",
  tone: "inspiring",
  gender: "female",
  word_count: 95,
  performance_score: 9.1,
  views: 180000,
  ctr: 0.14,
  created_at: datetime()
});

CREATE (s8:Script {
  id: "script_008",
  content: "콘텐츠 제작의 고민을 끝내드립니다. 매일 새로운 아이디어를 짜내느라 지치셨나요? AI Writer가 당신의 브랜드 톤에 맞는 스크립트를 자동 생성합니다. 과거 고성과 콘텐츠를 학습하여 일관성 있는 퀄리티를 보장하죠.",
  platform: "YouTube",
  tone: "professional",
  gender: "neutral",
  word_count: 105,
  performance_score: 8.6,
  views: 110000,
  ctr: 0.10,
  created_at: datetime()
});

CREATE (s9:Script {
  id: "script_009",
  content: "이거 실화? 5분 만에 영상 10개 만들기! 불가능해 보이지만 OmniVibe Pro로는 가능합니다. 템플릿 선택, 스크립트 입력, 렌더링 클릭. 끝! 이제 시간은 전략 수립에 투자하고, 제작은 AI에게 맡기세요.",
  platform: "TikTok",
  tone: "energetic",
  gender: "male",
  word_count: 88,
  performance_score: 9.3,
  views: 450000,
  ctr: 0.17,
  created_at: datetime()
});

CREATE (s10:Script {
  id: "script_010",
  content: "성공하는 콘텐츠의 비밀을 알려드립니다. 첫 3초가 승부를 결정합니다. 강력한 훅으로 시선을 사로잡고, 명확한 메시지로 가치를 전달하세요. CTA는 구체적으로! OmniVibe Pro의 Director Agent가 모든 걸 최적화해드립니다.",
  platform: "YouTube",
  tone: "professional",
  gender: "female",
  word_count: 98,
  performance_score: 8.9,
  views: 130000,
  ctr: 0.12,
  created_at: datetime()
});

// ==================== Relationships ====================

// Scripts belong to Campaigns
MATCH (s1:Script {id: "script_001"}), (c1:Campaign {id: "campaign_001"})
CREATE (s1)-[:BELONGS_TO]->(c1);

MATCH (s2:Script {id: "script_002"}), (c1:Campaign {id: "campaign_001"})
CREATE (s2)-[:BELONGS_TO]->(c1);

MATCH (s3:Script {id: "script_003"}), (c3:Campaign {id: "campaign_003"})
CREATE (s3)-[:BELONGS_TO]->(c3);

MATCH (s4:Script {id: "script_004"}), (c2:Campaign {id: "campaign_002"})
CREATE (s4)-[:BELONGS_TO]->(c2);

MATCH (s5:Script {id: "script_005"}), (c1:Campaign {id: "campaign_001"})
CREATE (s5)-[:BELONGS_TO]->(c1);

MATCH (s6:Script {id: "script_006"}), (c1:Campaign {id: "campaign_001"})
CREATE (s6)-[:BELONGS_TO]->(c1);

MATCH (s7:Script {id: "script_007"}), (c2:Campaign {id: "campaign_002"})
CREATE (s7)-[:BELONGS_TO]->(c2);

MATCH (s8:Script {id: "script_008"}), (c1:Campaign {id: "campaign_001"})
CREATE (s8)-[:BELONGS_TO]->(c1);

MATCH (s9:Script {id: "script_009"}), (c1:Campaign {id: "campaign_001"})
CREATE (s9)-[:BELONGS_TO]->(c1);

MATCH (s10:Script {id: "script_010"}), (c1:Campaign {id: "campaign_001"})
CREATE (s10)-[:BELONGS_TO]->(c1);

// ==================== Verification ====================

// Check node counts
MATCH (s:Script) RETURN count(s) AS total_scripts;
MATCH (c:Campaign) RETURN count(c) AS total_campaigns;

// Check high-performance scripts
MATCH (s:Script)
WHERE s.performance_score > 9.0
RETURN s.id, s.content, s.performance_score
ORDER BY s.performance_score DESC;
