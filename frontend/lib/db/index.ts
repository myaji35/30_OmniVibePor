import sqlite3 from 'sqlite3'
import { open, Database } from 'sqlite'
import path from 'path'
import fs from 'fs'

declare global {
    var sqliteDb: Database | undefined
}

let db: Database | null = null

export async function getDatabase(): Promise<Database> {
    if (global.sqliteDb) return global.sqliteDb
    if (db) return db

    const dbPath = path.join(process.cwd(), 'data', 'omnivibe.db')
    const dbDir = path.dirname(dbPath)

    // 데이터 디렉토리 생성
    if (!fs.existsSync(dbDir)) {
        fs.mkdirSync(dbDir, { recursive: true })
    }

    // 데이터베이스 연결
    db = await open({
        filename: dbPath,
        driver: sqlite3.Database
    })

    // 스키마 초기화
    await initializeSchema(db)

    // 개발 환경에서 Hot Reload 시 연결 유지
    if (process.env.NODE_ENV !== 'production') {
        global.sqliteDb = db
    }

    return db
}

async function initializeSchema(database: Database) {
    const schemaPath = path.join(process.cwd(), 'lib', 'db', 'schema.sql')

    if (fs.existsSync(schemaPath)) {
        const schema = fs.readFileSync(schemaPath, 'utf-8')
        await database.exec(schema)
        console.log('✅ Database schema initialized')
    }
}

export async function closeDatabase() {
    if (db) {
        await db.close()
        db = null
    }
}

// 데이터베이스 타입 정의
export interface Client {
    id?: number
    name: string
    brand_color?: string
    logo_url?: string
    industry?: string
    contact_email?: string
    created_at?: string
    updated_at?: string
}

export interface Campaign {
    id?: number
    name: string
    description?: string
    client_id?: number
    start_date?: string
    end_date?: string
    status?: 'active' | 'paused' | 'completed'
    // Concept Settings
    concept_gender?: string
    concept_tone?: string
    concept_style?: string
    target_duration?: number
    // Voice Settings
    voice_id?: string
    voice_name?: string
    // Intro/Outro Settings
    intro_video_url?: string
    intro_duration?: number
    outro_video_url?: string
    outro_duration?: number
    // BGM Settings
    bgm_url?: string
    bgm_volume?: number
    // Publishing Settings
    publish_schedule?: string
    auto_deploy?: boolean
    created_at?: string
    updated_at?: string
}

export interface ContentSchedule {
    id?: number
    campaign_id: number
    topic: string
    subtitle: string
    platform: 'Youtube' | 'Instagram' | 'TikTok' | 'Facebook'
    publish_date?: string
    status?: 'draft' | 'scheduled' | 'published' | 'archived'
    target_audience?: string
    keywords?: string
    notes?: string
    created_at?: string
    updated_at?: string
}

export interface GeneratedScript {
    id?: number
    content_id: number
    hook: string
    body: string
    cta: string
    total_duration?: number
    generated_at?: string
}

export interface StoryboardBlock {
    id?: number
    content_id: number
    block_number?: number
    type?: string
    start_time?: number
    end_time?: number
    duration?: number
    script?: string
    audio_url?: string
    // Background Settings
    background_type?: string
    background_url?: string
    background_source?: string
    // Character Settings
    character_enabled?: boolean
    character_url?: string
    character_start?: number
    character_duration?: number
    // Subtitle Settings
    subtitle_text?: string
    subtitle_preset?: string
    subtitle_position?: string
    // Transition Settings
    transition_effect?: string
    transition_duration?: number
    created_at?: string
    updated_at?: string
}

export interface ResourceLibrary {
    id?: number
    campaign_id?: number
    name: string
    type?: string
    url: string
    file_size?: number
    duration?: number
    width?: number
    height?: number
    usage?: string
    tags?: string
    usage_count?: number
    created_at?: string
    updated_at?: string
}
