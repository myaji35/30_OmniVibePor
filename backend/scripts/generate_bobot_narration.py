"""보봇(BoBot) 안전성 홍보 나레이션 — edge-tts 남성 (InJoon)"""
import edge_tts
import asyncio
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../frontend/public/insuregraph")

SCENES = [
    {
        "id": "bobot1",
        "text": "보봇은 왜 안전한가? AI 보험 상담, 정말 믿어도 될까요? 보봇의 다섯 가지 안전 장치를 소개합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "bobot2",
        "text": "첫째, 금소법 육대 원칙을 자동 준수합니다. 적합성 원칙, 적정성 원칙, 설명 의무, 불공정 영업 금지, 부당 권유 금지, 허위 과장 금지. 모든 상담 내용을 실시간으로 검증합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "bobot3",
        "text": "둘째, 모든 AI 판단에 법적 증빙을 남깁니다. ComplianceRecord에 상담 근거, 추천 이유, 고객 동의 내역을 자동 기록합니다. 금융감독원 검사에도 즉시 대응 가능합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "bobot4",
        "text": "셋째, GA법인의 관리 감독 하에 운영됩니다. 보봇은 독단적으로 계약을 체결하지 않습니다. 모든 최종 결정은 담당 설계사가 확인합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "bobot5",
        "text": "넷째, 삼만 팔천 개 약관을 학습했지만, 할루시네이션을 방지합니다. GraphRAG 기반으로 실제 약관 원문을 인용하며, 출처를 명시합니다.",
        "voice": "ko-KR-InJoonNeural",
        "rate": "-5%",
    },
    {
        "id": "bobot6",
        "text": "다섯째, 혁신금융서비스 샌드박스 기준으로 설계되었습니다. 금융위원회 승인 절차를 염두에 둔 아키텍처입니다. 보봇, 안전한 AI 보험 상담의 시작입니다.",
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

    full_text = " ".join(s["text"] for s in SCENES)
    full_comm = edge_tts.Communicate(text=full_text, voice="ko-KR-InJoonNeural", rate="-5%")
    full_path = os.path.join(OUTPUT_DIR, "bobot_narration_full.mp3")
    full_sub = edge_tts.SubMaker()
    with open(full_path, "wb") as f:
        async for chunk in full_comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                full_sub.feed(chunk)
    with open(os.path.join(OUTPUT_DIR, "bobot_narration_full.srt"), "w", encoding="utf-8") as f:
        f.write(full_sub.get_srt())
    print(f"\n  전체: {os.path.getsize(full_path)//1024}KB")
    print("✅ 보봇 안전성 나레이션 생성 완료!")


if __name__ == "__main__":
    asyncio.run(generate_all())
