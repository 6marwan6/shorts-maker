"""Decision 4 (2026-09-23): verify the real PySceneDetect distribution/import identity and pin
ContentDetector's configuration. This is a naming correction only -- SHOT_CONTENT_THRESHOLD=27.0,
SHOT_MIN_SCENE_FRAMES=15 and luma_only=False are unchanged from impl plan 4.3 / config@1.json.

Empirically verified 2026-09-23: `pyscenedetect` does not exist on PyPI at all
(`pip index versions pyscenedetect` -> "No matching distribution found"). `scenedetect` (0.7.1,
matching the plan's "0.7.x" line) is the real distribution; it imports as `scenedetect` and
exposes ContentDetector at scenedetect.detectors.content_detector.ContentDetector. This matches
the pre-authorized fallback ("if the distribution is scenedetect, use the verified distribution
identifier") -- not a silent substitution of a different detector/algorithm.
"""
import pytest
from shorts_config import load_config


def test_scenedetect_importable():
    import scenedetect  # noqa: F401


def test_pyscenedetect_does_not_exist_as_a_module():
    # Documents *why* pyproject.toml lists scenedetect, not pyscenedetect -- guards against
    # a future edit silently "fixing" the dependency name back to the plan's prose spelling.
    with pytest.raises(ModuleNotFoundError):
        import pyscenedetect  # noqa: F401


def test_content_detector_importable_and_constructible():
    from scenedetect.detectors import ContentDetector

    cfg = load_config()
    # Construction succeeding at all with these exact kwarg names is itself the contract check:
    # it proves threshold / min_scene_len / luma_only are valid parameter names on this pinned
    # version. _threshold is the one value ContentDetector stores as a plain attribute we can
    # assert on directly; min_scene_len is normalized internally (not exposed as a simple int
    # attribute in 0.7.x), so we check it via the constructor's own declared signature default
    # instead of reaching into a private/converted internal representation.
    import inspect

    sig = inspect.signature(ContentDetector.__init__)
    assert sig.parameters["min_scene_len"].default == cfg["SHOT_MIN_SCENE_FRAMES"] == 15

    detector = ContentDetector(
        threshold=cfg["SHOT_CONTENT_THRESHOLD"],
        min_scene_len=cfg["SHOT_MIN_SCENE_FRAMES"],
        luma_only=False,
    )
    assert detector._threshold == cfg["SHOT_CONTENT_THRESHOLD"] == 27.0


def test_installed_scenedetect_version_matches_0_7_x_line():
    import scenedetect
    assert scenedetect.__version__.startswith("0.7"), scenedetect.__version__
