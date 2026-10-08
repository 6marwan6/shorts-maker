"""Regression tests for canonical_json@1 (owner decision, 2026-09-23).

These are the committed fixtures a future TypeScript implementation must reproduce
byte-for-byte and hash-for-hash once the frontend exists (impl plan 0.3 is not built yet).
"""
import math

import pytest
from shorts_config import CANONICAL_JSON_VERSION, canonical_json, sha256_bytes

FIXTURES = [
    ({}, b"{}"),
    ({"b": 1, "a": 2}, b'{"a":2,"b":1}'),
    ({"a": [3, 1, 2]}, b'{"a":[3,1,2]}'),  # arrays: order preserved, not sorted
    ({"a": {"z": 1, "y": {"b": 2, "a": 1}}}, b'{"a":{"y":{"a":1,"b":2},"z":1}}'),  # nested sort
    ({"s": "café \u00e9"}, '{"s":"café é"}'.encode()),  # unicode kept literal, not \\uXXXX
    ({"n": None, "t": True, "f": False}, b'{"f":false,"n":null,"t":true}'),
    ({"a": 1.5}, b'{"a":1.5}'),
]


def test_canonical_json_version_is_pinned():
    assert CANONICAL_JSON_VERSION == "canonical_json@1"


@pytest.mark.parametrize("obj,expected_bytes", FIXTURES)
def test_canonical_json_matches_fixed_fixture(obj, expected_bytes):
    assert canonical_json(obj) == expected_bytes


@pytest.mark.parametrize("obj,expected_bytes", FIXTURES)
def test_canonical_json_hash_matches_fixed_fixture(obj, expected_bytes):
    assert sha256_bytes(canonical_json(obj)) == sha256_bytes(expected_bytes)


def test_key_insertion_order_does_not_affect_output():
    a = {"z": 1, "a": 2, "m": 3}
    b = {"a": 2, "m": 3, "z": 1}
    assert canonical_json(a) == canonical_json(b)


def test_nested_structures_preserve_array_order_but_sort_object_keys():
    obj = {"list": [{"z": 1, "a": 2}, {"b": 3}], "obj": {"z": 1, "a": 2}}
    out = canonical_json(obj).decode("utf-8")
    assert out == '{"list":[{"a":2,"z":1},{"b":3}],"obj":{"a":2,"z":1}}'


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(bad):
    with pytest.raises(ValueError):
        canonical_json({"x": bad})


def test_no_incidental_whitespace():
    out = canonical_json({"a": 1, "b": [1, 2, 3]})
    assert b" " not in out and b"\n" not in out and b"\t" not in out


def test_config_change_changes_hash_deterministically():
    a = canonical_json({"x": 1})
    b = canonical_json({"x": 2})
    assert sha256_bytes(a) != sha256_bytes(b)


def test_finite_special_floats_still_serialize():
    assert canonical_json({"x": 0.0}) == b'{"x":0.0}'
    assert math.isfinite(0.0)
