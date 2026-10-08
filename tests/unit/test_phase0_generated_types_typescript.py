"""TypeScript types are GENERATED from JSON Schema (impl plan 0.4/4.3), the TS counterpart of
test_phase0_generated_types.py. Regenerate with
`pnpm --filter @shorts-maker/schemas-typescript generate` after any schema change.

Requires the Node/pnpm toolchain (packages/schemas/typescript/node_modules) -- skipped with a
clear reason when that toolchain hasn't been installed, rather than silently passing.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "packages/schemas/json"
TS_PKG_DIR = ROOT / "packages/schemas/typescript"
GEN_DIR = TS_PKG_DIR / "src"

_NODE_MODULES_PRESENT = (TS_PKG_DIR / "node_modules").is_dir() and shutil.which("node") is not None

pytestmark = pytest.mark.skipif(
    not _NODE_MODULES_PRESENT,
    reason="Node/pnpm toolchain not installed (run `pnpm install` at repo root) -- TypeScript "
           "generation cannot be verified without it.",
)


def test_every_top_level_schema_has_a_generated_ts_type():
    skip = {"_identity.schema.json"}
    schemas = {p.name.replace(".schema.json", "") for p in SCHEMA_DIR.glob("*.schema.json") if p.name not in skip}
    generated = {p.stem for p in GEN_DIR.glob("*.ts")}
    assert schemas == generated, f"missing or stale generated TS types: {schemas ^ generated}"


def test_generated_typescript_types_are_up_to_date():
    # Runs the real generator's --check mode, which regenerates in memory and compares against
    # what's committed in src/ -- same principle as the Python up-to-date test, using the real
    # json-schema-to-typescript toolchain rather than a second, competing implementation.
    result = subprocess.run(
        ["node", "scripts/gen-types.mjs", "--check"], cwd=TS_PKG_DIR,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
