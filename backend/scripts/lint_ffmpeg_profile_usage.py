#!/usr/bin/env python3
"""
ISS-043 — ffmpeg cmd가 ios_safe_* 호출을 포함하는지 ast lint

ISS-042의 회귀 surface 1번 방어:
> "새 ffmpeg cmd 추가 시 모듈 안 쓰고 직접 옵션 작성"

이 lint는 backend/app/services 안의 모든 .py 파일을 ast로 파싱하여
다음 패턴을 검출한다:

위반 패턴:
    cmd = ["ffmpeg", "-y", ..., "-c:v", "libx264", ...]  # 직접 하드코딩
    →  ios_safe_*() 호출 없으면 위반

허용 패턴:
    cmd = ["ffmpeg", "-y", ...]
    cmd.extend(ios_safe_video_encoder_args(...))  # 모듈 사용 → OK

    또는 capability check / probe (인코딩 옵션 무관 + 짧은 cmd):
        ["ffmpeg", "-version"]
        ["ffmpeg", "-hide_banner", "-encoders"]

사용법:
    python3 backend/scripts/lint_ffmpeg_profile_usage.py
    → 위반 0건이면 exit 0
    → 위반 1건 이상이면 exit 1 + 위반 위치 출력

CI 통합:
    pre-commit hook 또는 .github/workflows/ffmpeg_lint.yml에 등록
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List, Tuple

# 검사 대상 디렉터리 (이 lint는 backend/app/services 한정)
TARGET_DIR = Path(__file__).resolve().parent.parent / "app" / "services"

# 모듈 함수 prefix — 이 prefix로 시작하는 호출이 같은 함수 안에 있으면 OK
IOS_SAFE_PREFIX = "ios_safe_"

# 명백히 인코딩 무관한 짧은 ffmpeg cmd (probe/version 등) 화이트리스트
SHORT_PROBE_PATTERNS = {
    ("-version",),
    ("-hide_banner", "-encoders"),
    ("-hide_banner", "-version"),
    ("-encoders",),
    ("-codecs",),
    ("-formats",),
    ("-buildconf",),
}

# 인코딩 관련 옵션 — 이게 cmd에 있으면 ios_safe_* 호출 필수
ENCODING_OPTIONS = {
    "-c:v", "-c:a", "-vcodec", "-acodec",
    "-pix_fmt", "-profile:v", "-level:v", "-vsync",
    "-r", "-b:v", "-b:a", "-ar",
}


# ─────────────────────────────────────────────────────────────────────────────
# Visitor
# ─────────────────────────────────────────────────────────────────────────────

class FFmpegLintVisitor(ast.NodeVisitor):
    """
    파일 단위로 visit:
        - 함수/메서드 별로 ffmpeg cmd literal 탐지
        - 같은 함수 안에 ios_safe_* 호출이 있는지 확인
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.violations: List[Tuple[int, str, str]] = []  # (line, func_name, snippet)
        self._func_stack: List[str] = []
        # 함수별 ios_safe 호출 위치 캐시
        self._func_has_ios_safe: dict[str, bool] = {}
        # 함수별 ffmpeg literal 위치
        self._func_ffmpeg_literals: dict[str, List[Tuple[int, list]]] = {}

    # ── 함수 진입/이탈 ──────────────────────────────────────────────────
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_func(node)
        self.generic_visit(node)
        self._exit_func(node)

    def _enter_func(self, node) -> None:
        qual = ".".join(self._func_stack + [node.name])
        self._func_stack.append(qual)
        self._func_has_ios_safe.setdefault(qual, False)
        self._func_ffmpeg_literals.setdefault(qual, [])

    def _exit_func(self, node) -> None:
        qual = self._func_stack.pop()
        # 함수 종료 시점에 위반 판단
        literals = self._func_ffmpeg_literals.get(qual, [])
        has_ios_safe = self._func_has_ios_safe.get(qual, False)
        for lineno, cmd_strs in literals:
            if self._is_short_probe(cmd_strs):
                continue  # capability check 화이트리스트
            if not self._has_encoding_options(cmd_strs):
                # 인코딩 옵션 없는 cmd (예: concat-c-copy)는 ios_safe 권장이지만 강제 X
                continue
            if not has_ios_safe:
                snippet = " ".join(cmd_strs[:6]) + (" ..." if len(cmd_strs) > 6 else "")
                self.violations.append((lineno, qual, snippet))

    # ── List literal 탐지 (ffmpeg cmd) ───────────────────────────────────
    def visit_List(self, node: ast.List) -> None:
        if not self._func_stack:
            self.generic_visit(node)
            return

        # 첫 element가 "ffmpeg" 문자열 리터럴인지
        if (
            node.elts
            and isinstance(node.elts[0], ast.Constant)
            and isinstance(node.elts[0].value, str)
            and node.elts[0].value == "ffmpeg"
        ):
            # 모든 string 리터럴 추출
            cmd_strs: list = []
            for el in node.elts:
                if isinstance(el, ast.Constant) and isinstance(el.value, str):
                    cmd_strs.append(el.value)
                elif isinstance(el, ast.Starred):
                    cmd_strs.append("*")  # *inputs 같은 unpack
            qual = self._func_stack[-1]
            self._func_ffmpeg_literals[qual].append((node.lineno, cmd_strs))

        self.generic_visit(node)

    # ── ios_safe_* 호출 탐지 ──────────────────────────────────────────────
    def visit_Call(self, node: ast.Call) -> None:
        if self._func_stack:
            qual = self._func_stack[-1]
            name = self._call_name(node.func)
            if name and name.startswith(IOS_SAFE_PREFIX):
                self._func_has_ios_safe[qual] = True
        self.generic_visit(node)

    def _call_name(self, func) -> str | None:
        # ios_safe_video_encoder_args(...) → "ios_safe_video_encoder_args"
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    # ── 화이트리스트/조건 헬퍼 ───────────────────────────────────────────
    def _is_short_probe(self, cmd_strs: list) -> bool:
        """
        capability check / probe 같은 짧은 cmd인지.
        cmd_strs[0] == "ffmpeg" 가정.
        """
        if len(cmd_strs) > 6:
            return False
        tail = tuple(cmd_strs[1:])
        # 화이트리스트 패턴 매칭 (앞부분 일치)
        for pattern in SHORT_PROBE_PATTERNS:
            if tail[: len(pattern)] == pattern:
                return True
        return False

    def _has_encoding_options(self, cmd_strs: list) -> bool:
        """cmd에 인코딩 관련 옵션이 하나라도 있는가."""
        return any(s in ENCODING_OPTIONS for s in cmd_strs)


# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────

def lint_file(path: Path) -> List[Tuple[Path, int, str, str]]:
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[WARN] {path}: read failed ({e})", file=sys.stderr)
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        print(f"[WARN] {path}: syntax error ({e})", file=sys.stderr)
        return []
    visitor = FFmpegLintVisitor(path)
    visitor.visit(tree)
    return [(path, line, fn, snippet) for (line, fn, snippet) in visitor.violations]


def main() -> int:
    if not TARGET_DIR.exists():
        print(f"[ERROR] target dir not found: {TARGET_DIR}", file=sys.stderr)
        return 2

    py_files = sorted(TARGET_DIR.rglob("*.py"))
    # ffmpeg_profile.py 자체는 검사 대상에서 제외 (정의처)
    # macOS resource fork 파일 (._*)도 제외
    py_files = [
        p for p in py_files
        if p.name != "ffmpeg_profile.py" and not p.name.startswith("._")
    ]

    print(f"[lint_ffmpeg_profile_usage] scanning {len(py_files)} files in {TARGET_DIR}")

    all_violations: List[Tuple[Path, int, str, str]] = []
    for f in py_files:
        all_violations.extend(lint_file(f))

    if not all_violations:
        print(f"  ✅ 0 violations — all ffmpeg cmds use ios_safe_* helpers (or are probes)")
        return 0

    print(f"  ❌ {len(all_violations)} violation(s) found:")
    print()
    for path, line, func, snippet in all_violations:
        try:
            rel = path.relative_to(TARGET_DIR.parent.parent.parent)
        except ValueError:
            rel = path
        print(f"  {rel}:{line}  in {func}()")
        print(f"      cmd starts with: {snippet}")
        print(f"      → 이 함수에 ios_safe_* 호출이 없습니다.")
        print(f"        backend/app/services/ffmpeg_profile.py 의 헬퍼를 사용하세요:")
        print(f"        cmd.extend(ios_safe_video_encoder_args(...))")
        print(f"        cmd.extend(ios_safe_video_output_args(...))")
        print(f"        cmd.extend(ios_safe_audio_encoder_args(...))")
        print()

    print(f"[lint_ffmpeg_profile_usage] FAILED — see violations above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
