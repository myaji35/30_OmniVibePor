"""chopd 나레이션 생성 — edge-tts (무료, API 키 불필요)"""
import edge_tts
import asyncio
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../frontend/public/chopd")

SCENES = [
    {
        "id": "scene1",
        "text": "AI가 당신의 브랜드를 관리합니다. 블로그, SNS, 쇼핑몰을 하나로. AI 콘텐츠를 자동 생성하고 예약 발행합니다.",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-5%",
    },
    {
        "id": "scene2",
        "text": "AI 대시보드에서 모든 채널을 한눈에 관리하세요. 오백 명 이상의 사용자가 선택한 플랫폼입니다.",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-5%",
    },
    {
        "id": "scene3",
        "text": "데스크톱과 모바일, 어디서든 완벽한 반응형 경험. 이동 중에도 브랜드를 관리하세요.",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-5%",
    },
    {
        "id": "scene4",
        "text": "올인원 랜딩 페이지로 서비스 소개부터 고객 확보까지. 코딩 없이 5분이면 완성됩니다.",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-5%",
    },
    {
        "id": "scene5",
        "text": "당신의 AI 파트너, 아임PD 하나면 충분합니다. 블로그, SNS, 쇼핑몰, 콘텐츠 자동 생성, 예약 발행까지.",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-5%",
    },
    {
        "id": "scene6",
        "text": "지금 바로 무료로 시작하세요. 신용카드 없이, 삼분이면 시작할 수 있습니다. chopd 점 io.",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-10%",
    },
]


async def generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timing_data = []

    for scene in SCENES:
        mp3_path = os.path.join(OUTPUT_DIR, f"narr_{scene['id']}.mp3")
        vtt_path = os.path.join(OUTPUT_DIR, f"narr_{scene['id']}.vtt")

        communicate = edge_tts.Communicate(
            text=scene["text"],
            voice=scene["voice"],
            rate=scene["rate"],
        )

        submaker = edge_tts.SubMaker()
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(submaker.get_srt())

        size = os.path.getsize(mp3_path)
        print(f"  {scene['id']}: {size // 1024}KB")
        timing_data.append({
            "id": scene["id"],
            "text": scene["text"],
            "mp3": f"narr_{scene['id']}.mp3",
            "vtt": f"narr_{scene['id']}.vtt",
        })

    # 전체 나레이션
    full_text = " ".join(s["text"] for s in SCENES)
    full_comm = edge_tts.Communicate(
        text=full_text, voice="ko-KR-SunHiNeural", rate="-5%",
    )
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

    size = os.path.getsize(full_path)
    print(f"\n  전체: {size // 1024}KB")

    with open(os.path.join(OUTPUT_DIR, "narration_meta.json"), "w", encoding="utf-8") as f:
        json.dump(timing_data, f, ensure_ascii=False, indent=2)

    print("✅ 나레이션 생성 완료!")


if __name__ == "__main__":
    asyncio.run(generate_all())
