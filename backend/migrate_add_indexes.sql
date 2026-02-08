-- OmniVibe Pro - Database 인덱스 추가 (성능 최적화)
-- 실행: sqlite3 omni_db.sqlite < migrate_add_indexes.sql

-- ==================== Campaigns ====================

CREATE INDEX IF NOT EXISTS idx_campaigns_client_id
ON campaigns(client_id);

CREATE INDEX IF NOT EXISTS idx_campaigns_status
ON campaigns(status);

CREATE INDEX IF NOT EXISTS idx_campaigns_platform
ON campaigns(platform);

CREATE INDEX IF NOT EXISTS idx_campaigns_created_at
ON campaigns(created_at DESC);

-- ==================== Contents ====================

CREATE INDEX IF NOT EXISTS idx_contents_campaign_id
ON contents(campaign_id);

CREATE INDEX IF NOT EXISTS idx_contents_status
ON contents(status);

CREATE INDEX IF NOT EXISTS idx_contents_created_at
ON contents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_contents_published_at
ON contents(published_at DESC);

-- Composite index for filtering by campaign + status
CREATE INDEX IF NOT EXISTS idx_contents_campaign_status
ON contents(campaign_id, status);

-- ==================== Script Blocks ====================

CREATE INDEX IF NOT EXISTS idx_script_blocks_content_id
ON script_blocks(content_id);

CREATE INDEX IF NOT EXISTS idx_script_blocks_sequence
ON script_blocks(content_id, sequence);

-- ==================== Audio Generations ====================

CREATE INDEX IF NOT EXISTS idx_audio_generations_content_id
ON audio_generations(content_id);

CREATE INDEX IF NOT EXISTS idx_audio_generations_task_id
ON audio_generations(task_id);

CREATE INDEX IF NOT EXISTS idx_audio_generations_status
ON audio_generations(status);

CREATE INDEX IF NOT EXISTS idx_audio_generations_created_at
ON audio_generations(created_at DESC);

-- ==================== Performance Metrics ====================

CREATE INDEX IF NOT EXISTS idx_performance_content_id
ON performance_metrics(content_id);

CREATE INDEX IF NOT EXISTS idx_performance_recorded_at
ON performance_metrics(recorded_at DESC);

-- ==================== A/B Tests ====================

CREATE INDEX IF NOT EXISTS idx_ab_tests_content_id
ON ab_tests(content_id);

CREATE INDEX IF NOT EXISTS idx_ab_tests_variant_type
ON ab_tests(variant_type);

-- ==================== Resources ====================

CREATE INDEX IF NOT EXISTS idx_resources_campaign_id
ON resources(campaign_id);

CREATE INDEX IF NOT EXISTS idx_resources_type
ON resources(resource_type);

-- ==================== 완료 ====================

SELECT 'Database indexes created successfully!' AS status;
