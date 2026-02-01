#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

# 스크립트 읽기
with open('test_script.txt', 'r', encoding='utf-8') as f:
    script_text = f.read()

print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📝 스크립트 길이: {len(script_text)} 글자")
print("")

start_time = time.time()

# API 호출
response = requests.post(
    'http://localhost:8000/api/v1/audio/generate',
    json={
        'text': script_text,
        'accuracy_threshold': 0.95,
        'max_attempts': 5
    }
)

result = response.json()
task_id = result['task_id']
print(f"📌 작업 ID: {task_id}")
print("⏱️  진행 상황 모니터링 중...")
print("")

# 상태 체크
while True:
    status_response = requests.get(f'http://localhost:8000/api/v1/audio/status/{task_id}')
    status_data = status_response.json()
    status = status_data['status']

    print(f"  상태: {status}", end='')

    if status == 'SUCCESS':
        print(" ✅")
        result_info = status_data.get('result', {})
        print(f"\n📊 최종 결과:")
        print(f"  - 시도 횟수: {result_info.get('attempts', 'N/A')}")
        print(f"  - 유사도: {result_info.get('final_similarity', 0) * 100:.2f}%")
        print(f"  - 오디오 경로: {result_info.get('audio_path', 'N/A')}")
        break
    elif status == 'FAILURE':
        print(" ❌")
        print(f"\n⚠️ 실패: {status_data.get('error', 'Unknown error')}")
        break
    else:
        print()

    time.sleep(2)

end_time = time.time()
elapsed = int(end_time - start_time)

print(f"\n⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏱️  총 소요 시간: {elapsed}초 ({elapsed // 60}분 {elapsed % 60}초)")
