"""Generate prompts/*.txt byte-for-byte from the fenced blocks in the v5.0 product plan (impl plan 0.8, 9.5).

hook_prompt@1 is written to prompts/hook_analysis_prompt@1.txt per impl plan 0.8/9.5 (filename
intentionally differs from the prompt's own version tag; the file is still a verbatim copy).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/spec/virality_shorts_plan_v5_0.md"
TARGETS = {
    "verifier_prompt@2": ROOT / "prompts/verifier_prompt@2.txt",
    "style_prompt@1": ROOT / "prompts/style_prompt@1.txt",
    "hook_prompt@1": ROOT / "prompts/hook_analysis_prompt@1.txt",
}


def extract(spec_text: str, marker: str) -> str:
    m = re.search(r"Prompt `" + re.escape(marker) + r"`:\*{0,2}\s*```text\n(.*?)\n```", spec_text, re.DOTALL)
    if not m:
        raise SystemExit(f"prompt block not found: {marker}")
    return m.group(1) + "\n"


def main() -> int:
    text = SPEC.read_text(encoding="utf-8")
    for marker, path in TARGETS.items():
        path.write_text(extract(text, marker), encoding="utf-8", newline="\n")
        print("wrote", path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
