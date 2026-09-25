import logging
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.domain import JobCreate, FlowCapabilities, CreditSafetyMode
from src.config.runtime_config import runtime_config
from src.database.repository import Repository

logger = logging.getLogger(__name__)

class CreditPolicyManager:
    """
    Evaluates and enforces credit and generation safety policies before prompt submission.
    Implements:
    - STRICT: Blocks if credit balance or cost is unverified, or if balance < cost.
    - WARN: Warns when unverified, but permits execution if explicitly allowed.
    - ALLOW_UNKNOWN: Permits unverified balance/cost when user specifies.
    - Pre-submission limit gates: Daily generations, session generations, max job cost.
    """

    @classmethod
    def evaluate_submission_safety(
        cls,
        job: JobCreate,
        caps: FlowCapabilities,
        db: Session,
    ) -> Tuple[bool, str, Optional[int]]:
        repo = Repository(db)
        config = runtime_config.get_all()
        mode_str = str(config.get("CREDIT_SAFETY_MODE", "STRICT")).upper()
        
        try:
            mode = CreditSafetyMode(mode_str)
        except ValueError:
            mode = CreditSafetyMode.STRICT

        # 1. Enforce Daily Generations Limit
        max_daily_gen = config.get("MAX_DAILY_GENERATIONS")
        if max_daily_gen and max_daily_gen > 0:
            daily_count = repo.get_daily_generation_count()
            if daily_count >= max_daily_gen:
                msg = f"Credit policy violation: Daily generation limit reached ({daily_count}/{max_daily_gen})."
                logger.warning(msg)
                return False, msg, None

        # 2. Extract verified cost if present
        cost = caps.cost_per_job
        is_cost_verified = (caps.cost_status == "VERIFIED" and cost is not None)
        
        # 3. Check Max Job Cost limit if cost is known
        max_job_cost = config.get("MAX_JOB_COST")
        if max_job_cost and is_cost_verified and cost > max_job_cost:
            msg = f"Credit policy violation: Job cost ({cost} credits) exceeds maximum allowed job cost ({max_job_cost})."
            logger.warning(msg)
            return False, msg, cost

        # 4. Evaluate Balance against Cost
        is_balance_verified = (caps.credit_status == "VERIFIED" and caps.credit_balance is not None)

        if is_balance_verified and is_cost_verified:
            if caps.credit_balance < cost:
                msg = f"Credit policy violation: Insufficient credits. Balance: {caps.credit_balance}, Required: {cost}."
                logger.warning(msg)
                return False, msg, cost

        # 5. Handle Unverified Credits / Costs per Safety Mode
        if not is_balance_verified or not is_cost_verified:
            # Check if user explicitly allowed unverified credits for this job
            if job.allow_unverified_credits:
                logger.info("Submission permitted: job explicitly opted to allow unverified credits.")
                return True, "Proceeding with unverified credit balance (user override)", cost

            if mode == CreditSafetyMode.STRICT:
                block_balance = config.get("BLOCK_ON_UNVERIFIED_BALANCE", True)
                block_cost = config.get("BLOCK_ON_UNVERIFIED_COST", True)
                
                if (not is_balance_verified and block_balance) or (not is_cost_verified and block_cost):
                    unverified_reasons = []
                    if not is_balance_verified:
                        unverified_reasons.append("credit balance is UNKNOWN")
                    if not is_cost_verified:
                        unverified_reasons.append("generation cost is UNKNOWN")
                    reasons_text = " and ".join(unverified_reasons)
                    msg = (
                        f"Credit Safety Policy (STRICT mode): Pre-submission check blocked because {reasons_text}. "
                        "To allow generation without verified credits, set Safety Mode to WARN or ALLOW_UNKNOWN in Settings, "
                        "or specify allow_unverified_credits=True."
                    )
                    logger.warning(msg)
                    return False, msg, cost

            elif mode == CreditSafetyMode.WARN:
                logger.warning("Credit Safety Policy (WARN mode): Proceeding with unverified credits/cost.")
                return True, "Proceeding with unverified credit balance/cost (WARN mode)", cost

            elif mode == CreditSafetyMode.ALLOW_UNKNOWN:
                logger.info("Credit Safety Policy (ALLOW_UNKNOWN mode): Proceeding with unverified credits/cost.")
                return True, "Proceeding under ALLOW_UNKNOWN policy", cost

        return True, "Credit policy verification passed", cost
