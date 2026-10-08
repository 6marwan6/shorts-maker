"""Phase 0 unit tests: JSON Schemas are valid draft 2020-12 and require v5.0's identity fields."""
import glob
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO / "packages/schemas/json"
FILES = sorted(glob.glob(str(SCHEMA_DIR / "*.schema.json")))


@pytest.mark.parametrize("path", FILES)
def test_schema_is_valid_draft_2020_12(path):
    Draft202012Validator.check_schema(json.loads(Path(path).read_bytes()))


# OWNER DECISION (2026-09-23, resolves former Q-01): render_profile_v1 keeps profile_version,
# not stage_version -- stage_version is pipeline-stage/producer provenance; profile_version is
# export-profile identity. This is a deliberate, permanent exception to the blanket identity-field
# rule below, not an unresolved gap. Excluded from that generic check with this documented reason.
IDENTITY_EXEMPT = {"render_profile_v1.schema.json"}

# Embedded sub-objects, not top-level artifacts: they carry no independent config/schema identity
# of their own (they inherit their parent artifact's), per each file's own description field.
SUB_OBJECT_SCHEMAS = {"boundary_event.schema.json", "edit_unit.schema.json", "super_unit.schema.json"}


@pytest.mark.parametrize(
    "path", [f for f in FILES if not f.endswith("_identity.schema.json")
             and Path(f).name not in IDENTITY_EXEMPT and Path(f).name not in SUB_OBJECT_SCHEMAS]
)
def test_schema_required_fields_include_identity(path):
    schema = json.loads(Path(path).read_bytes())
    required = set(schema.get("required", []))
    for f in ("schema_version", "stage_version", "config_version", "config_sha256"):
        assert f in required, f"{path} missing required identity field {f}"


@pytest.mark.parametrize("path", [f for f in FILES if not f.endswith("_identity.schema.json")])
def test_schema_unknown_field_policy_is_closed(path):
    # every top-level object schema explicitly closes additionalProperties (or documents why not).
    # _identity.schema.json is a reference-only fragment, never instantiated standalone, so it is
    # exempt from this check.
    schema = json.loads(Path(path).read_bytes())
    assert schema.get("additionalProperties") is False, path


def test_render_profile_v1_uses_profile_version_not_stage_version():
    # Owner decision 2026-09-23: distinct, non-interchangeable fields. Regression test requested
    # explicitly so the two are never accidentally substituted for one another.
    schema = json.loads((SCHEMA_DIR / "render_profile_v1.schema.json").read_bytes())
    assert "profile_version" in schema["required"]
    assert "stage_version" not in schema["required"]
    assert "profile_version" in schema["properties"]
    assert "stage_version" not in schema["properties"]


def test_other_artifacts_use_stage_version_not_profile_version():
    # The inverse check: every OTHER artifact schema keeps stage_version and does not
    # borrow render_profile_v1's profile_version field.
    for path in FILES:
        name = Path(path).name
        if name in ("_identity.schema.json",) or name in IDENTITY_EXEMPT or name in SUB_OBJECT_SCHEMAS:
            continue
        schema = json.loads(Path(path).read_bytes())
        assert "stage_version" in schema["required"], name
        assert "profile_version" not in schema.get("properties", {}), name
