import { getDatabase, Client, Campaign, ContentSchedule, GeneratedScript, StoryboardBlock, ResourceLibrary } from './index'
import fs from 'fs'
import path from 'path'

// ==================== 클라이언트 관련 함수 ====================
export async function getAllClients(): Promise<Client[]> {
    const db = await getDatabase()
    return db.all('SELECT * FROM clients ORDER BY created_at DESC')
}

export async function getClientById(id: number): Promise<Client | undefined> {
    const db = await getDatabase()
    return db.get('SELECT * FROM clients WHERE id = ?', id)
}

export async function createClient(client: Omit<Client, 'id'>): Promise<number> {
    const db = await getDatabase()
    const result = await db.run(
        'INSERT INTO clients (name, brand_color, logo_url, industry, contact_email) VALUES (?, ?, ?, ?, ?)',
        client.name,
        client.brand_color,
        client.logo_url,
        client.industry,
        client.contact_email
    )
    return result.lastID!
}

export async function updateClient(id: number, updates: Partial<Client>): Promise<void> {
    const db = await getDatabase()
    const fields = Object.keys(updates).filter(k => k !== 'id')
    const values = fields.map(k => updates[k as keyof Client])

    const setClause = fields.map(f => `${f} = ?`).join(', ')
    await db.run(
        `UPDATE clients SET ${setClause} WHERE id = ?`,
        ...values,
        id
    )
}

export async function deleteClient(id: number): Promise<void> {
    const db = await getDatabase()
    await db.run('DELETE FROM clients WHERE id = ?', id)
}

// ==================== 캠페인 관련 함수 ====================
export async function getAllCampaigns(): Promise<Campaign[]> {
    const db = await getDatabase()
    return db.all('SELECT * FROM campaigns ORDER BY created_at DESC')
}

export async function getCampaignById(id: number): Promise<Campaign | undefined> {
    const db = await getDatabase()
    return db.get('SELECT * FROM campaigns WHERE id = ?', id)
}

export async function createCampaign(campaign: Omit<Campaign, 'id'>): Promise<Campaign> {
    const db = await getDatabase()
    const result = await db.run(
        `INSERT INTO campaigns (
            name, description, client_id, start_date, end_date, status,
            concept_gender, concept_tone, concept_style, target_duration,
            voice_id, voice_name,
            intro_video_url, intro_duration, outro_video_url, outro_duration,
            bgm_url, bgm_volume,
            publish_schedule, auto_deploy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        campaign.name,
        campaign.description,
        campaign.client_id,
        campaign.start_date,
        campaign.end_date,
        campaign.status || 'active',
        campaign.concept_gender,
        campaign.concept_tone,
        campaign.concept_style,
        campaign.target_duration,
        campaign.voice_id,
        campaign.voice_name,
        campaign.intro_video_url,
        campaign.intro_duration || 5,
        campaign.outro_video_url,
        campaign.outro_duration || 5,
        campaign.bgm_url,
        campaign.bgm_volume || 0.3,
        campaign.publish_schedule,
        campaign.auto_deploy ? 1 : 0
    )

    // 생성된 캠페인 조회 및 반환
    const campaignId = result.lastID!
    const createdCampaign = await getCampaignById(campaignId)

    if (!createdCampaign) {
        throw new Error(`Campaign not found after creation: ${campaignId}`)
    }

    return createdCampaign
}

export async function updateCampaign(id: number, updates: Partial<Campaign>): Promise<void> {
    const db = await getDatabase()
    const fields = Object.keys(updates).filter(k => k !== 'id')
    const values = fields.map(k => {
        const value = updates[k as keyof Campaign]
        // Boolean을 SQLite INTEGER로 변환
        if (k === 'auto_deploy' && typeof value === 'boolean') {
            return value ? 1 : 0
        }
        return value
    })

    const setClause = fields.map(f => `${f} = ?`).join(', ')
    await db.run(
        `UPDATE campaigns SET ${setClause} WHERE id = ?`,
        ...values,
        id
    )
}

export async function deleteCampaign(id: number): Promise<void> {
    const db = await getDatabase()
    await db.run('DELETE FROM campaigns WHERE id = ?', id)
}

export async function getCampaignsByClient(clientId: number): Promise<Campaign[]> {
    const db = await getDatabase()
    return db.all('SELECT * FROM campaigns WHERE client_id = ? ORDER BY created_at DESC', clientId)
}

// 콘텐츠 스케줄 관련 함수
export async function getAllContentSchedules(): Promise<ContentSchedule[]> {
    const db = await getDatabase()
    return db.all(`
    SELECT cs.*, c.name as campaign_name 
    FROM content_schedule cs
    LEFT JOIN campaigns c ON cs.campaign_id = c.id
    ORDER BY cs.publish_date DESC
  `)
}

export async function getContentSchedulesByCampaign(campaignId: number): Promise<ContentSchedule[]> {
    const db = await getDatabase()
    return db.all(
        'SELECT * FROM content_schedule WHERE campaign_id = ? ORDER BY publish_date',
        campaignId
    )
}

export async function getContentScheduleById(id: number): Promise<ContentSchedule | undefined> {
    const db = await getDatabase()
    return db.get('SELECT * FROM content_schedule WHERE id = ?', id)
}

export async function createContentSchedule(content: Omit<ContentSchedule, 'id'>): Promise<number> {
    const db = await getDatabase()
    const result = await db.run(
        `INSERT INTO content_schedule 
    (campaign_id, topic, subtitle, platform, publish_date, status, target_audience, keywords, notes) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        content.campaign_id,
        content.topic,
        content.subtitle,
        content.platform,
        content.publish_date,
        content.status || 'draft',
        content.target_audience,
        content.keywords,
        content.notes
    )
    return result.lastID!
}

export async function updateContentSchedule(id: number, updates: Partial<ContentSchedule>): Promise<void> {
    const db = await getDatabase()
    const fields = Object.keys(updates).filter(k => k !== 'id')
    const values = fields.map(k => updates[k as keyof ContentSchedule])

    const setClause = fields.map(f => `${f} = ?`).join(', ')
    await db.run(
        `UPDATE content_schedule SET ${setClause} WHERE id = ?`,
        ...values,
        id
    )
}

// 생성된 스크립트 관련 함수
export async function getScriptByContentId(contentId: number): Promise<GeneratedScript | undefined> {
    const db = await getDatabase()
    return db.get(
        'SELECT * FROM generated_scripts WHERE content_id = ? ORDER BY generated_at DESC LIMIT 1',
        contentId
    )
}

export async function saveGeneratedScript(script: Omit<GeneratedScript, 'id'>): Promise<number> {
    const db = await getDatabase()
    const result = await db.run(
        `INSERT INTO generated_scripts (content_id, hook, body, cta, total_duration) 
    VALUES (?, ?, ?, ?, ?)`,
        script.content_id,
        script.hook,
        script.body,
        script.cta,
        script.total_duration
    )
    return result.lastID!
}

// ==================== 스토리보드 블록 관련 함수 ====================
export async function getStoryboardBlocksByContentId(contentId: number): Promise<StoryboardBlock[]> {
    const db = await getDatabase()
    return db.all(
        'SELECT * FROM storyboard_blocks WHERE content_id = ? ORDER BY block_number',
        contentId
    )
}

export async function getStoryboardBlockById(id: number): Promise<StoryboardBlock | undefined> {
    const db = await getDatabase()
    return db.get('SELECT * FROM storyboard_blocks WHERE id = ?', id)
}

export async function createStoryboardBlock(block: Omit<StoryboardBlock, 'id'>): Promise<number> {
    const db = await getDatabase()
    const result = await db.run(
        `INSERT INTO storyboard_blocks (
            content_id, block_number, type, start_time, end_time, duration, script, audio_url,
            background_type, background_url, background_source,
            character_enabled, character_url, character_start, character_duration,
            subtitle_text, subtitle_preset, subtitle_position,
            transition_effect, transition_duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        block.content_id,
        block.block_number,
        block.type,
        block.start_time,
        block.end_time,
        block.duration,
        block.script,
        block.audio_url,
        block.background_type,
        block.background_url,
        block.background_source,
        block.character_enabled ? 1 : 0,
        block.character_url,
        block.character_start,
        block.character_duration,
        block.subtitle_text,
        block.subtitle_preset,
        block.subtitle_position || 'bottom',
        block.transition_effect,
        block.transition_duration || 0.5
    )
    return result.lastID!
}

export async function updateStoryboardBlock(id: number, updates: Partial<StoryboardBlock>): Promise<void> {
    const db = await getDatabase()
    const fields = Object.keys(updates).filter(k => k !== 'id')
    const values = fields.map(k => {
        const value = updates[k as keyof StoryboardBlock]
        // Boolean을 SQLite INTEGER로 변환
        if (k === 'character_enabled' && typeof value === 'boolean') {
            return value ? 1 : 0
        }
        return value
    })

    const setClause = fields.map(f => `${f} = ?`).join(', ')
    await db.run(
        `UPDATE storyboard_blocks SET ${setClause} WHERE id = ?`,
        ...values,
        id
    )
}

export async function deleteStoryboardBlock(id: number): Promise<void> {
    const db = await getDatabase()
    await db.run('DELETE FROM storyboard_blocks WHERE id = ?', id)
}

export async function deleteStoryboardBlocksByContentId(contentId: number): Promise<void> {
    const db = await getDatabase()
    await db.run('DELETE FROM storyboard_blocks WHERE content_id = ?', contentId)
}

// ==================== 리소스 라이브러리 관련 함수 ====================
export async function getAllResources(): Promise<ResourceLibrary[]> {
    const db = await getDatabase()
    return db.all('SELECT * FROM resource_library ORDER BY created_at DESC')
}

export async function getResourcesByCampaign(campaignId: number): Promise<ResourceLibrary[]> {
    const db = await getDatabase()
    return db.all(
        'SELECT * FROM resource_library WHERE campaign_id = ? ORDER BY created_at DESC',
        campaignId
    )
}

export async function getResourcesByType(type: string): Promise<ResourceLibrary[]> {
    const db = await getDatabase()
    return db.all(
        'SELECT * FROM resource_library WHERE type = ? ORDER BY created_at DESC',
        type
    )
}

export async function getResourceById(id: number): Promise<ResourceLibrary | undefined> {
    const db = await getDatabase()
    return db.get('SELECT * FROM resource_library WHERE id = ?', id)
}

export async function createResource(resource: Omit<ResourceLibrary, 'id'>): Promise<number> {
    const db = await getDatabase()
    const result = await db.run(
        `INSERT INTO resource_library (
            campaign_id, name, type, url, file_size, duration, width, height, usage, tags, usage_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        resource.campaign_id,
        resource.name,
        resource.type,
        resource.url,
        resource.file_size,
        resource.duration,
        resource.width,
        resource.height,
        resource.usage,
        resource.tags,
        resource.usage_count || 0
    )
    return result.lastID!
}

export async function updateResource(id: number, updates: Partial<ResourceLibrary>): Promise<void> {
    const db = await getDatabase()
    const fields = Object.keys(updates).filter(k => k !== 'id')
    const values = fields.map(k => updates[k as keyof ResourceLibrary])

    const setClause = fields.map(f => `${f} = ?`).join(', ')
    await db.run(
        `UPDATE resource_library SET ${setClause} WHERE id = ?`,
        ...values,
        id
    )
}

export async function deleteResource(id: number): Promise<void> {
    const db = await getDatabase()
    await db.run('DELETE FROM resource_library WHERE id = ?', id)
}

export async function incrementResourceUsage(id: number): Promise<void> {
    const db = await getDatabase()
    await db.run(
        'UPDATE resource_library SET usage_count = usage_count + 1 WHERE id = ?',
        id
    )
}

export async function searchResources(query: string): Promise<ResourceLibrary[]> {
    const db = await getDatabase()
    return db.all(
        `SELECT * FROM resource_library
        WHERE name LIKE ? OR tags LIKE ? OR usage LIKE ?
        ORDER BY created_at DESC`,
        `%${query}%`,
        `%${query}%`,
        `%${query}%`
    )
}

// ==================== 데이터베이스 초기화 (샘플 데이터 포함) ====================
export async function seedDatabase(): Promise<void> {
    const db = await getDatabase()
    const seedPath = path.join(process.cwd(), 'lib', 'db', 'seed.sql')

    if (fs.existsSync(seedPath)) {
        const seedSQL = fs.readFileSync(seedPath, 'utf-8')
        await db.exec(seedSQL)
        console.log('✅ Sample data seeded')
    }
}

// 검색 함수
export async function searchContentSchedules(query: string): Promise<ContentSchedule[]> {
    const db = await getDatabase()
    return db.all(
        `SELECT cs.*, c.name as campaign_name 
    FROM content_schedule cs
    LEFT JOIN campaigns c ON cs.campaign_id = c.id
    WHERE cs.topic LIKE ? OR cs.subtitle LIKE ? OR cs.keywords LIKE ?
    ORDER BY cs.publish_date DESC`,
        `%${query}%`,
        `%${query}%`,
        `%${query}%`
    )
}
