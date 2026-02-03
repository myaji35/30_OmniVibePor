fetch('http://localhost:3020/api/writer-generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content_id: 999,
    campaign_name: '테스트 캠페인',
    topic: 'AI 기술의 발전',
    platform: 'YouTube',
    target_duration: 30,
    regenerate: false
  })
})
.then(res => res.json())
.then(data => {
  console.log('\n✅ API 응답 성공!')
  console.log('Success:', data.success)
  console.log('Source:', data.source)
  console.log('Cached:', data.cached)
  console.log('\n📝 생성된 스크립트 미리보기:')
  console.log('Hook:', data.hook?.substring(0, 100) + '...')
  console.log('Body:', data.body?.substring(0, 100) + '...')
  console.log('CTA:', data.cta?.substring(0, 100) + '...')
  console.log('\n📊 메타데이터:')
  console.log(JSON.stringify(data.metadata, null, 2))
})
.catch(err => {
  console.error('❌ API 호출 실패:', err.message)
})
