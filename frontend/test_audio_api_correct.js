// 오디오 생성 API 테스트 (올바른 파라미터)
const testScript = "안녕하세요, 오디오 생성 테스트입니다."

fetch('http://localhost:8000/api/v1/audio/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: testScript,
    voice_id: "rachel",
    language: 'ko',
    accuracy_threshold: 0.95,
    max_attempts: 3
  })
})
.then(res => res.json())
.then(data => {
  console.log('\n📊 오디오 생성 API 응답:')
  console.log(JSON.stringify(data, null, 2))
  
  if (data.task_id) {
    console.log(`\n✅ Task ID: ${data.task_id}`)
    console.log('⏳ 비동기 작업이 시작되었습니다')
    console.log('💡 상태 확인: curl http://localhost:8000/api/v1/audio/status/' + data.task_id)
  } else if (data.detail) {
    console.log(`\n❌ 오류:`, data.detail)
  } else if (data.error) {
    console.log(`\n❌ 오류: ${data.error}`)
  }
})
.catch(err => {
  console.error('❌ API 호출 실패:', err.message)
})
