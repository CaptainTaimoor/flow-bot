import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.models.domain import JobCreate, FlowCapabilities
from src.flow.credit_policy import CreditPolicyManager
from src.config.runtime_config import runtime_config

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_strict_mode_blocks_unknown_balance(db_session, monkeypatch):
    monkeypatch.setattr(runtime_config, "get_all", lambda: {
        "CREDIT_SAFETY_MODE": "STRICT",
        "BLOCK_ON_UNVERIFIED_BALANCE": True,
        "BLOCK_ON_UNVERIFIED_COST": True,
        "MAX_DAILY_GENERATIONS": 20,
    })

    job = JobCreate(prompt="A test prompt", allow_unverified_credits=False)
    caps = FlowCapabilities(credit_balance=None, credit_status="UNKNOWN", cost_status="UNKNOWN")

    allowed, reason, cost = CreditPolicyManager.evaluate_submission_safety(job, caps, db_session)
    assert allowed is False
    assert "Pre-submission check blocked" in reason
    assert "credit balance is UNKNOWN" in reason

def test_strict_mode_allowed_with_user_override(db_session, monkeypatch):
    monkeypatch.setattr(runtime_config, "get_all", lambda: {
        "CREDIT_SAFETY_MODE": "STRICT",
        "BLOCK_ON_UNVERIFIED_BALANCE": True,
        "BLOCK_ON_UNVERIFIED_COST": True,
        "MAX_DAILY_GENERATIONS": 20,
    })

    job = JobCreate(prompt="A test prompt", allow_unverified_credits=True)
    caps = FlowCapabilities(credit_balance=None, credit_status="UNKNOWN", cost_status="UNKNOWN")

    allowed, reason, cost = CreditPolicyManager.evaluate_submission_safety(job, caps, db_session)
    assert allowed is True
    assert "user override" in reason.lower()

def test_warn_mode_permits_unverified(db_session, monkeypatch):
    monkeypatch.setattr(runtime_config, "get_all", lambda: {
        "CREDIT_SAFETY_MODE": "WARN",
        "BLOCK_ON_UNVERIFIED_BALANCE": True,
        "BLOCK_ON_UNVERIFIED_COST": True,
        "MAX_DAILY_GENERATIONS": 20,
    })

    job = JobCreate(prompt="A test prompt", allow_unverified_credits=False)
    caps = FlowCapabilities(credit_balance=None, credit_status="UNKNOWN", cost_status="UNKNOWN")

    allowed, reason, cost = CreditPolicyManager.evaluate_submission_safety(job, caps, db_session)
    assert allowed is True
    assert "WARN mode" in reason

def test_insufficient_credits_blocks(db_session, monkeypatch):
    monkeypatch.setattr(runtime_config, "get_all", lambda: {
        "CREDIT_SAFETY_MODE": "STRICT",
        "MAX_DAILY_GENERATIONS": 20,
    })

    job = JobCreate(prompt="A test prompt")
    caps = FlowCapabilities(
        credit_balance=5,
        credit_status="VERIFIED",
        cost_per_job=20,
        cost_status="VERIFIED",
    )

    allowed, reason, cost = CreditPolicyManager.evaluate_submission_safety(job, caps, db_session)
    assert allowed is False
    assert "Insufficient credits" in reason
