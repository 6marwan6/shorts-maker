"""Phase 0 unit tests: prompt files are byte-identical to the v5.0 fenced blocks (impl plan 0.8)."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPEC = (REPO / "docs/spec/virality_shorts_plan_v5_0.md").read_text(encoding="utf-8")

CASES = [
    ("verifier_prompt@2", REPO / "prompts/verifier_prompt@2.txt"),
    ("style_prompt@1", REPO / "prompts/style_prompt@1.txt"),
    ("hook_prompt@1", REPO / "prompts/hook_analysis_prompt@1.txt"),
]


def _spec_block(marker: str) -> str:
    m = re.search(r"Prompt `" + re.escape(marker) + r"`:\*{0,2}\s*```text\n(.*?)\n```", SPEC, re.DOTALL)
    assert m, f"block for {marker} not found in spec"
    return m.group(1) + "\n"


def test_prompt_files_match_v5_source_exactly():
    for marker, path in CASES:
        assert path.read_text(encoding="utf-8") == _spec_block(marker), marker


def test_prompt_files_end_with_single_trailing_newline():
    for _, path in CASES:
        raw = path.read_bytes()
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")


def test_verifier_prompt_contains_no_pre_region_context_language():
    # v4.5/R24: viewer-only judge, no pre-region context sent
    text = (REPO / "prompts/verifier_prompt@2.txt").read_text()
    assert "The viewer has seen nothing except this short" in text
