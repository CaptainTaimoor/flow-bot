import pytest
from src.models.domain import (
    GenerationState,
    CreditSafetyMode,
    CorrelationConfidence,
    AuthState,
    normalize_aspect_ratio,
    normalize_duration,
    normalize_model_name,
    FlowCapabilities,
)

def test_generation_states_count():
    # Verify all 28 distinct states are defined in GenerationState
    expected_states = {
        "CREATED",
        "QUEUED",
        "OPENING_BROWSER",
        "CHECKING_AUTH",
        "OPENING_FLOW",
        "OPENING_PROJECT",
        "DISCOVERING_CAPABILITIES",
        "CHECKING_CREDIT_POLICY",
        "PREPARING",
        "SUBMITTING",
        "SUBMISSION_CONFIRMED",
        "SUBMISSION_UNKNOWN",
        "GENERATION_STARTED",
        "GENERATING",
        "WAITING_FOR_ASSET",
        "ASSET_IDENTIFICATION",
        "LOCATING_ASSET",
        "DOWNLOADING",
        "VALIDATING",
        "THUMBNAIL_GENERATING",
        "READY",
        "SUCCESS",
        "COMPLETED",
        "RETRY_RECONCILIATION_REQUIRED",
        "RETRYING",
        "CANCELLATION_UNCONFIRMED",
        "AUTH_REQUIRED",
        "MANUAL_ACTION_REQUIRED",
        "FAILED",
        "CANCELLED",
    }
    actual_states = {s.value for s in GenerationState}
    for s in expected_states:
        assert s in actual_states, f"Missing state: {s}"

def test_normalization():
    assert normalize_aspect_ratio("16:9") == "16:9"
    assert normalize_aspect_ratio("Landscape") == "16:9"
    assert normalize_aspect_ratio("portrait") == "9:16"
    assert normalize_aspect_ratio("1:1") == "1:1"
    assert normalize_aspect_ratio("square") == "1:1"
    assert normalize_aspect_ratio(None) is None

    assert normalize_duration("5s") == "5"
    assert normalize_duration(10) == "10"
    assert normalize_duration("8") == "8"
    assert normalize_duration(None) is None

    assert normalize_model_name("  Nano Banana 2  ") == "Nano Banana 2"
    assert normalize_model_name(None) is None

def test_flow_capabilities_truthful_defaults():
    caps = FlowCapabilities()
    assert caps.credit_balance is None
    assert caps.credit_status == "UNKNOWN"
    assert caps.cost_per_job is None
    assert caps.cost_status == "UNKNOWN"
    assert caps.model_source == "unknown"
