/**
 * Database Connector — ISS-036 Phase 0-D
 *
 * PG 우선 + SQLite fallback 듀얼 커넥터.
 * 환경변수 DATABASE_URL이 postgresql:// 로 시작하면 PG,
 * 아니면 기존 SQLite (frontend/data/omnivibe.db) 사용.
 *
 * service.ts 호환을 위해 동일한 인터페이스 유지:
 *   db.all(sql, ...params)  → SELECT 결과 배열
 *   db.get(sql, ...params)  → SELECT 첫 행 또는 undefined
 *   db.run(sql, ...params)  → { lastID, changes }
 */
import { Pool } from 'pg'

// -- SQLite imports (fallback용, 동적 import로 PG 전용 환경에서 에러 방지)
let sqliteOpen: any = null
let sqlite3Driver: any = null

// -- 타입 정의 (기존 호환)
export interface DbResult {
  lastID?: number
  changes?: number
}

export interface DbAdapter {
  all<T = any>(sql: string, ...params: any[]): Promise<T[]>
  get<T = any>(sql: string, ...params: any[]): Promise<T | undefined>
  run(sql: string, ...params: any[]): Promise<DbResult>
  exec(sql: string): Promise<void>
  close(): Promise<void>
}

// -- PG Adapter
class PgAdapter implements DbAdapter {
  private pool: Pool

  constructor(connectionString: string) {
    this.pool = new Pool({ connectionString })
  }

  async all<T = any>(sql: string, ...params: any[]): Promise<T[]> {
    const pgSql = sqliteParamsToPg(sql)
    const { rows } = await this.pool.query(pgSql, params)
    return rows as T[]
  }

  async get<T = any>(sql: string, ...params: any[]): Promise<T | undefined> {
    const pgSql = sqliteParamsToPg(sql)
    const { rows } = await this.pool.query(pgSql + (pgSql.includes('LIMIT') ? '' : ' LIMIT 1'), params)
    return rows[0] as T | undefined
  }

  async run(sql: string, ...params: any[]): Promise<DbResult> {
    const pgSql = sqliteParamsToPg(sql)
    const result = await this.pool.query(pgSql + ' RETURNING id', params).catch(async () => {
      // RETURNING이 실패하는 경우 (UPDATE/DELETE 등) 재시도
      return this.pool.query(pgSql, params)
    })
    return {
      lastID: result.rows?.[0]?.id,
      changes: result.rowCount ?? 0,
    }
  }

  async exec(sql: string): Promise<void> {
    await this.pool.query(sql)
  }

  async close(): Promise<void> {
    await this.pool.end()
  }
}

// -- SQLite Adapter (기존 로직 래핑)
class SqliteAdapter implements DbAdapter {
  private db: any

  constructor(db: any) {
    this.db = db
  }

  async all<T = any>(sql: string, ...params: any[]): Promise<T[]> {
    return this.db.all(sql, ...params)
  }

  async get<T = any>(sql: string, ...params: any[]): Promise<T | undefined> {
    return this.db.get(sql, ...params)
  }

  async run(sql: string, ...params: any[]): Promise<DbResult> {
    const result = await this.db.run(sql, ...params)
    return { lastID: result.lastID, changes: result.changes }
  }

  async exec(sql: string): Promise<void> {
    await this.db.exec(sql)
  }

  async close(): Promise<void> {
    await this.db.close()
  }
}

// -- ? → $1, $2 파라미터 변환 (SQLite → PG)
function sqliteParamsToPg(sql: string): string {
  let idx = 0
  return sql.replace(/\?/g, () => `$${++idx}`)
}

// -- 싱글톤 DB 인스턴스
declare global {
  var dbAdapter: DbAdapter | undefined
}

let adapter: DbAdapter | null = null

export async function getDatabase(): Promise<DbAdapter> {
  if (global.dbAdapter) return global.dbAdapter
  if (adapter) return adapter

  const dbUrl = process.env.DATABASE_URL || ''

  if (dbUrl.startsWith('postgresql://') || dbUrl.startsWith('postgres://')) {
    // PG 모드
    console.log('🐘 Database: PostgreSQL')
    adapter = new PgAdapter(dbUrl)
  } else {
    // SQLite fallback
    console.log('📁 Database: SQLite (fallback)')
    const path = await import('path')
    const fs = await import('fs')
    const { open } = await import('sqlite')
    const sqlite3 = (await import('sqlite3')).default

    const dbPath = path.default.join(process.cwd(), 'data', 'omnivibe.db')
    const dbDir = path.default.dirname(dbPath)
    if (!fs.default.existsSync(dbDir)) {
      fs.default.mkdirSync(dbDir, { recursive: true })
    }

    const sqliteDb = await open({ filename: dbPath, driver: sqlite3.Database })

    // 스키마 초기화
    const schemaPath = path.default.join(process.cwd(), 'lib', 'db', 'schema.sql')
    if (fs.default.existsSync(schemaPath)) {
      const schema = fs.default.readFileSync(schemaPath, 'utf-8')
      await sqliteDb.exec(schema)
    }

    adapter = new SqliteAdapter(sqliteDb)
  }

  if (process.env.NODE_ENV !== 'production') {
    global.dbAdapter = adapter
  }

  return adapter
}

export async function closeDatabase() {
  if (adapter) {
    await adapter.close()
    adapter = null
    global.dbAdapter = undefined
  }
}

// -- 타입 정의 (기존 호환, re-export)
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
  concept_gender?: string
  concept_tone?: string
  concept_style?: string
  target_duration?: number
  voice_id?: string
  voice_name?: string
  intro_video_url?: string
  intro_duration?: number
  outro_video_url?: string
  outro_duration?: number
  bgm_url?: string
  bgm_volume?: number
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
  background_type?: string
  background_url?: string
  background_source?: string
  character_enabled?: boolean
  character_url?: string
  character_start?: number
  character_duration?: number
  subtitle_text?: string
  subtitle_preset?: string
  subtitle_position?: string
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
