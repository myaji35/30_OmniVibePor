"""InsureGraph Pro 나레이션 생성 — edge-tts 남성 음성 (InJoon)"""
import edge_tts
import asyncio
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../frontend/public/insuregraph")

SCENES = [
    {
        "id": "scene1",
        "text": "InsureGraph Pro. 삼만 팔천 팔백 팔십 팔개 약관을 학습한 AI가, 고객의 보장을 분석합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "scene2",
        "text": "AI 대시보드에서 전체 고객 현황을 한눈에 파악하세요. 오늘의 상담 일정, 보장 갱신 알림, 실적 현황까지.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "scene3",
        "text": "고객의 보장 내역을 AI가 자동으로 분석합니다. 카테고리별 보장 현황, 위험 등급, 개선 제안까지 원클릭으로.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "scene4",
        "text": "보장 갭 분석 리포트를 자동 생성합니다. 부족한 보장, 중복 보장, 추천 상품까지 고객 맞춤형 리포트를 제공합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "scene5",
        "text": "포트폴리오 분석으로 내 고객 전체를 조감하세요. 연령별, 지역별, 보장 유형별 분포를 시각화합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "scene6",
        "text": "지금 InsureGraph Pro를 시작하세요. GraphRAG 기반 보험 분석 AI로, 상담 품질을 혁신합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-10%",
    },
]


async def generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for scene in SCENES:
        mp3_path = os.path.join(OUTPUT_DIR, f"narr_{scene['id']}.mp3")
        communicate = edge_tts.Communicate(
            text=scene["text"], voice=scene["voice"], rate=scene["rate"],
        )
        submaker = edge_tts.SubMaker()
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)
        srt_path = os.path.join(OUTPUT_DIR, f"narr_{scene['id']}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(submaker.get_srt())
        print(f"  {scene['id']}: {os.path.getsize(mp3_path)//1024}KB")

    # 전체 나레이션
    full_text = " ".join(s["text"] for s in SCENES)
    full_comm = edge_tts.Communicate(text=full_text, voice="ko-KR-InJoonNeural", rate="-5%")
    full_path = os.path.join(OUTPUT_DIR, "narration_full.mp3")
    full_sub = edge_tts.SubMaker()
    with open(full_path, "wb") as f:
        async for chunk in full_comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                full_sub.feed(chunk)
    with open(os.path.join(OUTPUT_DIR, "narration_full.srt"), "w", encoding="utf-8") as f:
        f.write(full_sub.get_srt())
    print(f"\n  전체: {os.path.getsize(full_path)//1024}KB")
    print("✅ InsureGraph 나레이션 생성 완료!")


if __name__ == "__main__":
    asyncio.run(generate_all())
