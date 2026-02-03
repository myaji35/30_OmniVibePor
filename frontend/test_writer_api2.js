fetch('http://localhost:3020/api/writer-generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content_id: 888,
    campaign_name: '테스트 캠페인2',
    topic: '클라우드 컴퓨팅의 미래',
    platform: 'YouTube',
    target_duration: 45,
    regenerate: false
  })
})
.then(res => res.json())
.then(data => {
  console.log('\n✅ 전체 응답:')
  console.log(JSON.stringify(data, null, 2))
})
.catch(err => {
  console.error('❌ API 호출 실패:', err.message)
})
