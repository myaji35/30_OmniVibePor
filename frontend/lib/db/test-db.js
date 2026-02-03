#!/usr/bin/env node

/**
 * SQLite 데이터베이스 테스트 스크립트
 * 
 * 실행 방법:
 * node lib/db/test-db.js
 */

const sqlite3 = require('sqlite3').verbose()
const path = require('path')
const fs = require('fs')

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

// 스키마 실행
const schemaPath = path.join(__dirname, 'schema.sql')
const schema = fs.readFileSync(schemaPath, 'utf-8')

db.exec(schema, (err) => {
    if (err) {
        console.error('❌ Schema creation error:', err)
        process.exit(1)
    }
    console.log('✅ Schema created successfully')

    // 샘플 데이터 삽입
    const seedPath = path.join(__dirname, 'seed.sql')
    const seed = fs.readFileSync(seedPath, 'utf-8')

    db.exec(seed, (err) => {
        if (err) {
            console.error('❌ Seed data error:', err)
            process.exit(1)
        }
        console.log('✅ Sample data inserted')

        // 데이터 확인
        db.all('SELECT * FROM campaigns', (err, campaigns) => {
            if (err) {
                console.error('❌ Query error:', err)
                process.exit(1)
            }
            console.log('\n📊 Campaigns:')
            console.table(campaigns)

            db.all(`
        SELECT cs.*, c.name as campaign_name 
        FROM content_schedule cs
        LEFT JOIN campaigns c ON cs.campaign_id = c.id
      `, (err, schedules) => {
                if (err) {
                    console.error('❌ Query error:', err)
                    process.exit(1)
                }
                console.log('\n📅 Content Schedules:')
                console.table(schedules)

                db.all('SELECT * FROM generated_scripts', (err, scripts) => {
                    if (err) {
                        console.error('❌ Query error:', err)
                        process.exit(1)
                    }
                    console.log('\n📝 Generated Scripts:')
                    console.table(scripts)

                    console.log('\n✅ Database test completed successfully!')
                    console.log(`📁 Database location: ${dbPath}`)

                    db.close()
                })
            })
        })
    })
})
