"""Generate Python (and, once a TS toolchain exists, TypeScript) types from packages/schemas/json/
(impl plan 0.4 / 4.3: "Generate Python and TypeScript types from the JSON Schemas; do not
maintain competing handwritten models.")

TypeScript generation is deliberately NOT wired here yet: it needs a Node/pnpm project
(impl plan 0.3, frontend scaffold) to run json-schema-to-typescript or quicktype against,
and none exists yet. Running Python generation alone, from the same schema files, keeps this
script honest about what it actually does today.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "packages/schemas/json"
OUT_DIR = ROOT / "packages/schemas/python"

# _identity.schema.json is a $ref-only fragment, not a standalone artifact -- generating a
# model class for it would create a type nothing actually instantiates.
SKIP = {"_identity.schema.json"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "__init__.py").touch()
    schemas = sorted(p for p in SCHEMA_DIR.glob("*.schema.json") if p.name not in SKIP)
    for schema in schemas:
        model_name = schema.stem.replace(".schema", "")
        out_file = OUT_DIR / f"{model_name}.py"
        cmd = [
            sys.executable, "-m", "datamodel_code_generator",
            "--input", str(schema),
            "--input-file-type", "jsonschema",
            "--output", str(out_file),
            "--output-model-type", "pydantic_v2.BaseModel",
            "--target-python-version", "3.12",
            "--use-schema-description",
            "--collapse-root-models",
            "--disable-timestamp",
            "--use-double-quotes",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"FAILED {schema.name}:\n{result.stderr}", file=sys.stderr)
            return 1
        print(f"generated {out_file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
