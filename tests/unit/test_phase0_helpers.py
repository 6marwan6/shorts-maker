"""Phase 0 unit tests: shared deterministic helpers (impl plan 2.3 / v5.0 2.36.0)."""
import math

from shorts_config import load_config, robust_z_v1


def test_robust_z_null_propagation():
    assert robust_z_v1(None, 0, 1, 0.01) is None
    assert robust_z_v1(1, None, 1, 0.01) is None
    assert robust_z_v1(1, 0, None, 0.01) is None


def test_robust_z_normal_case():
    # den = max(1.4826*mad, floor); mad=2 -> den = 2.9652
    z = robust_z_v1(x=10, center=4, mad=2, floor=0.01)
    assert math.isclose(z, 6 / (1.4826 * 2), rel_tol=1e-9)


def test_robust_z_floor_dominates_when_mad_small():
    z = robust_z_v1(x=1, center=0, mad=0, floor=0.5)
    assert math.isclose(z, 1 / 0.5)


def test_robust_z_zero_mad_zero_floor_equal_center():
    assert robust_z_v1(x=5, center=5, mad=0, floor=0) == 0


def test_robust_z_zero_mad_zero_floor_finite_fallback():
    cfg = load_config()
    z_pos = robust_z_v1(x=5, center=4, mad=0, floor=0)
    z_neg = robust_z_v1(x=3, center=4, mad=0, floor=0)
    assert z_pos == cfg["ROBUST_Z_ZERO_MAD"] == 6.0
    assert z_neg == -cfg["ROBUST_Z_ZERO_MAD"]


def test_robust_z_never_raises_divide_by_zero():
    # V7-2 / V8-2: shared finite robust_z_v1 must never blow up
    for x, c, m, f in [(0, 0, 0, 0), (100, 0, 0, 0), (-5, -5, 0, 0)]:
        v = robust_z_v1(x, c, m, f)
        assert v is not None and math.isfinite(v)
