"""Python types are GENERATED from JSON Schema (impl plan 0.4/4.3), never hand-maintained.
This test fails if someone hand-edits packages/schemas/python/*.py without regenerating --
regenerate with `python3 scripts/gen_types.py` after any schema change.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "packages/schemas/python"


def test_generated_python_types_are_up_to_date(tmp_path, monkeypatch):
    # Re-run the real generator against a copy of the schemas, writing into tmp_path, then
    # diff byte-for-byte against what's committed -- catches actual drift, not just "it runs".
    import shutil

    scratch_repo = tmp_path / "repo"
    shutil.copytree(ROOT / "packages/schemas/json", scratch_repo / "packages/schemas/json")
    (scratch_repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts/gen_types.py", scratch_repo / "scripts/gen_types.py")
    result = subprocess.run(
        [sys.executable, "scripts/gen_types.py"], cwd=scratch_repo,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    for committed in GEN_DIR.glob("*.py"):
        if committed.stem == "__init__":
            continue
        fresh = scratch_repo / "packages/schemas/python" / committed.name
        assert fresh.read_text() == committed.read_text(), f"{committed.name} is stale -- rerun scripts/gen_types.py"


def test_every_top_level_schema_has_a_generated_model():
    schema_dir = ROOT / "packages/schemas/json"
    skip = {"_identity.schema.json"}
    schemas = {p.stem.replace(".schema", "") for p in schema_dir.glob("*.schema.json") if p.name not in skip}
    generated = {p.stem for p in GEN_DIR.glob("*.py") if p.stem != "__init__"}
    assert schemas == generated, f"missing or stale generated models: {schemas ^ generated}"


def test_no_hand_authored_pydantic_models_outside_generated_dir():
    # guard against a competing handwritten model creeping in elsewhere in the repo
    for path in ROOT.rglob("*.py"):
        if GEN_DIR in path.parents or "node_modules" in str(path) or ".venv" in str(path):
            continue
        if path == ROOT / "tests/unit/test_phase0_generated_types.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "from pydantic import BaseModel" not in text or "class " not in text.split(
            "from pydantic import BaseModel", 1
        )[1][:200], f"possible hand-authored pydantic model in {path}"
