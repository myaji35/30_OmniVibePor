#!/usr/bin/env python3
"""PMF 인터뷰 결과 등록 헬퍼 — ISS-165.

인터뷰 메모(.md) 파일을 읽고 summary.md 표를 자동 갱신.
PMF 충족 카운트 5명 이상이면 ISS-154 unblock 후보 알림.

사용:
    python3 scripts/register_pmf_interview.py 01_marketing-agency-kim_260502.md \\
        --vertical medical-dermatology \\
        --q4 5 --q5 8000 --q8 60 --pmf yes
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERVIEWS_DIR = ROOT / "docs" / "05-research" / "pmf-interviews"
SUMMARY = INTERVIEWS_DIR / "summary.md"
THRESHOLD_PMF_COUNT = 5
THRESHOLD_INTERVIEW_COUNT = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="인터뷰 메모 파일명 (NN_role_YYMMDD.md)")
    parser.add_argument("--vertical", required=True)
    parser.add_argument("--q4", type=int, required=True, help="Q4 5점 척도")
    parser.add_argument("--q5", type=int, required=True, help="Q5 지불 의사 (원)")
    parser.add_argument("--q8", type=int, required=True, help="Q8 raw 영상 비율 (퍼센트)")
    parser.add_argument("--pmf", choices=["yes", "no"], required=True)
    parser.add_argument("--respondent", default="익명", help="응답자 이니셜")
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    args = parser.parse_args()

    file_path = INTERVIEWS_DIR / args.filename
    if not file_path.exists():
        sys.exit(f"인터뷰 파일 미존재: {file_path}")

    # 행 번호 추출 (NN_ prefix)
    m = re.match(r"(\d{2})_", args.filename)
    if not m:
        sys.exit(f"파일명 형식 오류 (NN_ prefix 필요): {args.filename}")
    row_num = int(m.group(1))
    if not (1 <= row_num <= 10):
        sys.exit(f"NN은 01~10 사이여야 함: {row_num}")

    text = SUMMARY.read_text(encoding="utf-8")
    pmf_emoji = "PASS" if args.pmf == "yes" else "FAIL"

    pattern = rf"^\| {row_num} \| \(대기\) \|.*$"
    new_row = (
        f"| {row_num} | {args.respondent} | {args.vertical} | {args.date} "
        f"| {args.q4} | {args.q5:,} | {args.q8} | {pmf_emoji} | "
        f"[{args.filename}]({args.filename}) |"
    )
    new_text, count = re.subn(pattern, new_row, text, count=1, flags=re.MULTILINE)
    if count == 0:
        sys.exit(f"행 {row_num} 갱신 실패 — 이미 등록되었거나 표 형식 변경 가능성")

    # PMF 카운트 재계산
    rows = re.findall(r"^\| (\d+) \| (?!\(대기\))(.*?) \|.*\| (PASS|FAIL) \|", new_text, re.MULTILINE)
    pmf_yes = sum(1 for r in rows if r[2] == "PASS")
    total = len(rows)
    new_text = re.sub(
        r"\*\*통과 카운트\*\*: \d+ / 10.*",
        f"**통과 카운트**: {pmf_yes} / 10 (목표: {THRESHOLD_PMF_COUNT}명 PMF YES) — 진행: {total}/10",
        new_text,
        count=1,
    )

    SUMMARY.write_text(new_text, encoding="utf-8")
    print(f"등록 완료: {args.filename}")
    print(f"  PMF 통과: {pmf_yes}/{total} (임계 {THRESHOLD_PMF_COUNT})")
    print(f"  진행: {total}/{THRESHOLD_INTERVIEW_COUNT}")

    if pmf_yes >= THRESHOLD_PMF_COUNT and total >= THRESHOLD_INTERVIEW_COUNT:
        print()
        print("=" * 60)
        print("[GATE G1 PASS 후보] ISS-154 BLOCKED_AT_GATE → READY 전환 가능")
        print("Cost Model G2 검증 후 Phase B 착수.")
        print("=" * 60)


if __name__ == "__main__":
    main()
