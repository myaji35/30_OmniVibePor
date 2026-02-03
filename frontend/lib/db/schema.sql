-- OmniVibe Pro - Content Schedule Database Schema
-- SQLite3 스키마 정의

-- 1. 클라이언트 테이블
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand_color TEXT,
    logo_url TEXT,
    industry TEXT,
    contact_email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 캠페인 테이블
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    client_id INTEGER,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'completed')),
    -- Concept Settings
    concept_gender TEXT,
    concept_tone TEXT,
    concept_style TEXT,
    target_duration INTEGER,
    -- Voice Settings
    voice_id TEXT,
    voice_name TEXT,
    -- Intro/Outro Settings
    intro_video_url TEXT,
    intro_duration INTEGER DEFAULT 5,
    outro_video_url TEXT,
    outro_duration INTEGER DEFAULT 5,
    -- BGM Settings
    bgm_url TEXT,
    bgm_volume REAL DEFAULT 0.3,
    -- Publishing Settings
    publish_schedule TEXT,
    auto_deploy INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
);

-- 3. 콘텐츠 스케줄 테이블
CREATE TABLE IF NOT EXISTS content_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    platform TEXT NOT NULL CHECK(platform IN ('Youtube', 'Instagram', 'TikTok', 'Facebook')),
    publish_date DATE,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'scheduled', 'published', 'archived')),
    target_audience TEXT,
    keywords TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- 4. 생성된 스크립트 테이블
CREATE TABLE IF NOT EXISTS generated_scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    hook TEXT NOT NULL,
    body TEXT NOT NULL,
    cta TEXT NOT NULL,
    total_duration INTEGER, -- 초 단위
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES content_schedule(id) ON DELETE CASCADE
);

-- 5. 스토리보드 블록 테이블
CREATE TABLE IF NOT EXISTS storyboard_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    block_number INTEGER,
    type TEXT,
    start_time REAL,
    end_time REAL,
    duration REAL,
    script TEXT,
    audio_url TEXT,
    -- Background Settings
    background_type TEXT,
    background_url TEXT,
    background_source TEXT,
    -- Character Settings
    character_enabled INTEGER DEFAULT 0,
    character_url TEXT,
    character_start REAL,
    character_duration REAL,
    -- Subtitle Settings
    subtitle_text TEXT,
    subtitle_preset TEXT,
    subtitle_position TEXT DEFAULT 'bottom',
    -- Transition Settings
    transition_effect TEXT,
    transition_duration REAL DEFAULT 0.5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES content_schedule(id) ON DELETE CASCADE
);

-- 6. 리소스 라이브러리 테이블
CREATE TABLE IF NOT EXISTS resource_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    name TEXT NOT NULL,
    type TEXT,
    url TEXT NOT NULL,
    file_size INTEGER,
    duration REAL,
    width INTEGER,
    height INTEGER,
    usage TEXT,
    tags TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

-- 7. 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client_id);
CREATE INDEX IF NOT EXISTS idx_content_campaign ON content_schedule(campaign_id);
CREATE INDEX IF NOT EXISTS idx_content_platform ON content_schedule(platform);
CREATE INDEX IF NOT EXISTS idx_content_publish_date ON content_schedule(publish_date);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_schedule(status);
CREATE INDEX IF NOT EXISTS idx_scripts_content ON generated_scripts(content_id);
CREATE INDEX IF NOT EXISTS idx_storyboard_content ON storyboard_blocks(content_id);
CREATE INDEX IF NOT EXISTS idx_storyboard_block_number ON storyboard_blocks(content_id, block_number);
CREATE INDEX IF NOT EXISTS idx_resource_campaign ON resource_library(campaign_id);
CREATE INDEX IF NOT EXISTS idx_resource_type ON resource_library(type);

-- 8. 트리거: updated_at 자동 업데이트
CREATE TRIGGER IF NOT EXISTS update_clients_timestamp
AFTER UPDATE ON clients
BEGIN
    UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
CREATE TRIGGER IF NOT EXISTS update_campaigns_timestamp 
AFTER UPDATE ON campaigns
BEGIN
    UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_content_timestamp
AFTER UPDATE ON content_schedule
BEGIN
    UPDATE content_schedule SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_storyboard_timestamp
AFTER UPDATE ON storyboard_blocks
BEGIN
    UPDATE storyboard_blocks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_resource_timestamp
AFTER UPDATE ON resource_library
BEGIN
    UPDATE resource_library SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
