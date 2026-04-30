"""Phase A 검증 스크립트 — overlay_generator 결과 정합성 점검.

기존 SubtitleEditor 출력(JSON 파일)이 있으면 word-level diff,
없으면 overlay_generator 단독 실행 + 결과 검증.

사용:
    python -m scripts.verify_overlay_parity --stt-json <path>
    python -m scripts.verify_overlay_parity --stt-json <path> --reference <path>

ISS-153 — Phase A 마무리 통합 검증.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_word_timestamps(stt_json_path: Path) -> list:
    """WordTimestamp 호환 dict 배열을 JSON 파일에서 로드한다.

    기대 포맷:
        [{"word": "안녕하세요", "start": 0.0, "end": 0.5}, ...]
    """
    with stt_json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"stt-json은 배열 형식이어야 합니다: {stt_json_path}")

    from app.services.overlay_generator_service import WordTimestamp

    words = []
    for item in data:
        words.append(
            WordTimestamp(
                word=item["word"],
                start=float(item["start"]),
                end=float(item["end"]),
                speaker_id=item.get("speaker_id"),
                confidence=item.get("confidence"),
            )
        )
    return words


def _run_overlay_generator(words: list) -> object:
    """OverlayGeneratorService.generate()를 실행하고 결과를 반환한다."""
    from app.services.overlay_generator_service import (
        OverlayGeneratorService,
        OverlayInput,
        OverlayStyle,
    )

    service = OverlayGeneratorService()
    input_data = OverlayInput(
        word_timestamps=words,
        style=OverlayStyle.subtitle,
        brand_tokens={},
    )
    return service.generate(input_data)


def _word_level_diff(generated_words: list[str], reference_words: list[str]) -> dict:
    """word-level diff 계산.

    Returns:
        {
            "total_words": int,
            "matched": int,
            "match_rate": float (0.0–1.0),
            "missing": list[str],
            "extra": list[str],
        }
    """
    gen_set = set(w.upper() for w in generated_words)
    ref_set = set(w.upper() for w in reference_words)

    matched = len(gen_set & ref_set)
    total = max(len(gen_set), len(ref_set), 1)
    match_rate = matched / total

    return {
        "total_words": total,
        "matched": matched,
        "match_rate": round(match_rate, 4),
        "missing": sorted(ref_set - gen_set),
        "extra": sorted(gen_set - ref_set),
    }


def _load_reference_words(reference_path: Path) -> list[str]:
    """SubtitleEditor 결과 JSON에서 단어 목록을 추출한다.

    기대 포맷 (SubtitleEditor 저장 형식):
        [{"text": "HELLO WORLD", "start": 0.0, "end": 1.0}, ...]
    또는 단어 배열:
        [{"word": "안녕하세요", "start": 0.0, "end": 0.5}, ...]
    """
    with reference_path.open(encoding="utf-8") as f:
        data = json.load(f)

    words: list[str] = []
    for item in data:
        if "text" in item:
            # SubtitleChunk 형식 — 공백 분할
            words.extend(item["text"].upper().split())
        elif "word" in item:
            words.append(item["word"].upper())
    return words


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase A overlay_generator 정합성 검증"
    )
    parser.add_argument(
        "--stt-json",
        required=True,
        help="WordTimestamp 배열 JSON 파일 경로",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="(선택) 기존 SubtitleEditor JSON 경로 — 있으면 word-level diff 수행",
    )
    args = parser.parse_args()

    stt_path = Path(args.stt_json)
    if not stt_path.exists():
        print(f"[ERROR] --stt-json 파일 없음: {stt_path}", file=sys.stderr)
        sys.exit(1)

    # 1. WordTimestamp 로드
    print(f"[INFO] stt-json 로드: {stt_path}")
    words = _load_word_timestamps(stt_path)
    print(f"[INFO] WordTimestamp: {len(words)}개")

    # 2. overlay_generator 실행
    print("[INFO] OverlayGeneratorService.generate() 실행...")
    output = _run_overlay_generator(words)
    print(f"[INFO] composition_id: {output.composition_id}")
    print(f"[INFO] duration_frames: {output.duration_frames}")
    print(f"[INFO] fps: {output.fps}")
    jsx_lines = len(output.remotion_jsx.splitlines())
    print(f"[INFO] remotion_jsx: {jsx_lines}줄")

    # 3. 단독 검증
    assert output.remotion_jsx.strip(), "[FAIL] remotion_jsx가 비어 있습니다"
    assert output.composition_id.startswith("overlay-"), (
        f"[FAIL] composition_id 형식 오류: {output.composition_id}"
    )
    assert output.duration_frames > 0, (
        f"[FAIL] duration_frames가 0 이하: {output.duration_frames}"
    )
    print("[PASS] overlay_generator 단독 검증 통과")

    # 4. reference가 있으면 word-level diff
    if args.reference:
        ref_path = Path(args.reference)
        if not ref_path.exists():
            print(f"[WARN] --reference 파일 없음: {ref_path} — diff 건너뜀")
        else:
            print(f"[INFO] reference 로드: {ref_path}")
            ref_words = _load_reference_words(ref_path)
            gen_words = [w.word for w in words]

            diff = _word_level_diff(gen_words, ref_words)
            print("\n[Word-Level Diff]")
            print(f"  total_words : {diff['total_words']}")
            print(f"  matched     : {diff['matched']}")
            print(f"  match_rate  : {diff['match_rate']:.1%}")
            if diff["missing"]:
                print(f"  missing     : {diff['missing'][:10]}")
            if diff["extra"]:
                print(f"  extra       : {diff['extra'][:10]}")

            if diff["match_rate"] < 0.8:
                print(f"[WARN] match_rate {diff['match_rate']:.1%} < 80% — 차이 확인 필요")
            else:
                print(f"[PASS] word-level diff match_rate {diff['match_rate']:.1%} >= 80%")

    print("\n[DONE] Phase A overlay parity 검증 완료")
    sys.exit(0)


if __name__ == "__main__":
    main()
