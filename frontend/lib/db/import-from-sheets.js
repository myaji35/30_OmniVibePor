#!/usr/bin/env node

/**
 * 구글 시트 데이터를 SQLite3로 이관하는 스크립트
 * 
 * 실행 방법:
 * node lib/db/import-from-sheets.js
 */

const sqlite3 = require('sqlite3').verbose()
const path = require('path')
const fs = require('fs')

// 구글 시트 데이터 (실제로는 Google Sheets API에서 가져옴)
const SHEET_DATA = [
    {
        '소제목': '저시력이란?',
        '캠페인명': '2026 시력 인식 캠페인',
        '플랫폼': 'Youtube',
        '발행일': '2026-02-15',
        '주제': '저시력 인식 개선',
        '타겟': '일반 대중',
        '키워드': '저시력, 시각장애, 인식개선'
    },
    {
        '소제목': '저시력 지원정책',
        '캠페인명': '2027 시력 인식 캠페인',
        '플랫폼': 'Youtube',
        '발행일': '2026-03-01',
        '주제': '정부 지원 정책 안내',
        '타겟': '저시력인 및 가족',
        '키워드': '지원정책, 복지, 정부지원'
    },
    {
        '소제목': '일상생활 팁',
        '캠페인명': '2028 시력 인식 캠페인',
        '플랫폼': 'Youtube',
        '발행일': '2026-03-15',
        '주제': '저시력인을 위한 생활 가이드',
        '타겟': '저시력인',
        '키워드': '생활팁, 보조기기, 일상생활'
    }
]

const dbPath = path.join(__dirname, '../../data/omnivibe.db')
const dbDir = path.dirname(dbPath)

// 데이터 디렉토리 생성
if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true })
    console.log('✅ Created data directory')
}

const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('❌ Database connection error:', err)
        process.exit(1)
    }
    console.log('✅ Connected to SQLite database')
})

// 스키마 초기화
const schemaPath = path.join(__dirname, 'schema.sql')
const schema = fs.readFileSync(schemaPath, 'utf-8')

db.exec(schema, (err) => {
    if (err) {
        console.error('❌ Schema creation error:', err)
        process.exit(1)
    }
    console.log('✅ Schema initialized')

    // 캠페인 맵 (캠페인명 -> ID)
    const campaignMap = new Map()

    // 1단계: 캠페인 추출 및 삽입
    const uniqueCampaigns = [...new Set(SHEET_DATA.map(row => row['캠페인명']))]

    console.log(`\n📊 Importing ${uniqueCampaigns.length} campaigns...`)

    const campaignPromises = uniqueCampaigns.map((campaignName, index) => {
        return new Promise((resolve, reject) => {
            db.run(
                `INSERT OR IGNORE INTO campaigns (name, description, status) VALUES (?, ?, ?)`,
                [campaignName, `${campaignName} 설명`, 'active'],
                function (err) {
                    if (err) {
                        reject(err)
                    } else {
                        // ID 가져오기
                        db.get('SELECT id FROM campaigns WHERE name = ?', [campaignName], (err, row) => {
                            if (err) {
                                reject(err)
                            } else {
                                campaignMap.set(campaignName, row.id)
                                console.log(`  ✓ ${campaignName} (ID: ${row.id})`)
                                resolve()
                            }
                        })
                    }
                }
            )
        })
    })

    Promise.all(campaignPromises).then(() => {
        console.log(`✅ ${uniqueCampaigns.length} campaigns imported`)

        // 2단계: 콘텐츠 스케줄 삽입
        console.log(`\n📅 Importing ${SHEET_DATA.length} content schedules...`)

        const contentPromises = SHEET_DATA.map((row, index) => {
            return new Promise((resolve, reject) => {
                const campaignId = campaignMap.get(row['캠페인명'])

                db.run(
                    `INSERT INTO content_schedule 
          (campaign_id, topic, subtitle, platform, publish_date, status, target_audience, keywords) 
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
                    [
                        campaignId,
                        row['주제'],
                        row['소제목'],
                        row['플랫폼'],
                        row['발행일'],
                        'scheduled',
                        row['타겟'] || null,
                        row['키워드'] || null
                    ],
                    function (err) {
                        if (err) {
                            reject(err)
                        } else {
                            console.log(`  ✓ [${index + 1}/${SHEET_DATA.length}] ${row['소제목']} (ID: ${this.lastID})`)
                            resolve(this.lastID)
                        }
                    }
                )
            })
        })

        Promise.all(contentPromises).then(() => {
            console.log(`✅ ${SHEET_DATA.length} content schedules imported`)

            // 3단계: 결과 확인
            db.all(`
        SELECT cs.id, cs.subtitle, c.name as campaign_name, cs.platform, cs.publish_date
        FROM content_schedule cs
        LEFT JOIN campaigns c ON cs.campaign_id = c.id
        ORDER BY cs.publish_date
      `, (err, rows) => {
                if (err) {
                    console.error('❌ Query error:', err)
                    process.exit(1)
                }

                console.log('\n📋 Imported Data Summary:')
                console.table(rows)

                console.log('\n✅ Import completed successfully!')
                console.log(`📁 Database location: ${dbPath}`)
                console.log(`📊 Total campaigns: ${uniqueCampaigns.length}`)
                console.log(`📅 Total content schedules: ${SHEET_DATA.length}`)

                db.close()
            })
        }).catch(err => {
            console.error('❌ Content import error:', err)
            db.close()
            process.exit(1)
        })
    }).catch(err => {
        console.error('❌ Campaign import error:', err)
        db.close()
        process.exit(1)
    })
})
