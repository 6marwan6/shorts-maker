"""Phase 1 unit tests: app.schemas request validation -- no DB, no network."""
import uuid

import pytest
from app.schemas import (
    CandidateEditRequest,
    CandidateReframeRequest,
    CreateJobRequest,
    CreateUploadRequest,
    RegisterRequest,
)
from pydantic import ValidationError


def test_candidate_edit_requires_at_least_one_operation():
    with pytest.raises(ValidationError):
        CandidateEditRequest(operations=[])


def test_candidate_edit_accepts_trim_start():
    req = CandidateEditRequest(operations=[{"type": "trim_start", "requested_source_ms": 500}])
    assert req.operations[0].type == "trim_start"


def test_candidate_edit_accepts_trim_end():
    req = CandidateEditRequest(operations=[{"type": "trim_end", "requested_source_ms": 500}])
    assert req.operations[0].type == "trim_end"


def test_candidate_edit_accepts_remove_retained_interval():
    seg_id = str(uuid.uuid4())
    req = CandidateEditRequest(operations=[{"type": "remove_retained_interval", "output_segment_id": seg_id}])
    assert str(req.operations[0].output_segment_id) == seg_id


def test_candidate_edit_rejects_unknown_operation_type():
    with pytest.raises(ValidationError):
        CandidateEditRequest(operations=[{"type": "delete_everything", "requested_source_ms": 0}])


def test_candidate_edit_rejects_negative_ms():
    with pytest.raises(ValidationError):
        CandidateEditRequest(operations=[{"type": "trim_start", "requested_source_ms": -1}])


def test_candidate_edit_accepts_multiple_operations_in_order():
    req = CandidateEditRequest(operations=[
        {"type": "trim_start", "requested_source_ms": 100},
        {"type": "trim_end", "requested_source_ms": 200},
    ])
    assert [op.type for op in req.operations] == ["trim_start", "trim_end"]


def test_reframe_request_defaults_to_auto():
    assert CandidateReframeRequest().strategy == "auto"


def test_reframe_request_rejects_unknown_strategy():
    with pytest.raises(ValidationError):
        CandidateReframeRequest(strategy="not_a_real_strategy")


@pytest.mark.parametrize("strategy", ["auto", "fixed_center", "face_aware", "multi_speaker", "blurred_background"])
def test_reframe_request_accepts_every_v5_0_strategy(strategy):
    assert CandidateReframeRequest(strategy=strategy).strategy == strategy


def test_register_request_rejects_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@example.com", password="short")


def test_register_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", password="a-long-enough-password")


def test_create_job_request_requires_export_profile_id():
    with pytest.raises(ValidationError):
        CreateJobRequest(source_video_id=str(uuid.uuid4()))


def test_create_upload_request_requires_filename_and_content_type():
    with pytest.raises(ValidationError):
        CreateUploadRequest(filename="", content_type="video/mp4")
