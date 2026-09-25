# Credit Safety Policy & Generation Limit Enforcement

## Overview
Google Flow utilizes an account-level credit system for AI media generation. Because credit replenishment and allocation rules are dynamic, this system implements a strict, configurable safety engine (`src/flow/credit_policy.py`) to prevent unexpected credit depletion, runaways, and unapproved spending.

---

## Credit Safety Modes (`CreditSafetyMode`)

Configured via the runtime setting or `.env` variable `CREDIT_SAFETY_MODE`:

### 1. `STRICT` (Recommended Default for Production)
- **Behavior:** Blocks job execution unless the credit cost and current credit balance are explicitly verified from Google Flow DOM, or the user provides an explicit `user_confirmed=True` flag for that specific submission.
- **Use Case:** Production environments where budget overruns must be strictly prevented.

### 2. `WARN`
- **Behavior:** Logs a prominent warning when credit cost or balance is unverified or unknown, but permits generation to proceed if within the daily and per-session job caps.
- **Use Case:** Staging and experimental environments where Google Flow UI variations may temporarily obscure credit badges.

### 3. `ALLOW_UNKNOWN`
- **Behavior:** Bypasses unverified credit cost checks entirely, relying solely on daily generation counts and concurrency limits.
- **Use Case:** Unattended automation suites running on unlimited or fixed-allowance enterprise plans.

---

## Safety Limits & Counters

The system enforces three concentric layers of limit gating before any prompt is typed into Google Flow:

1. **Concurrency Gate (`CONCURRENCY`, default = 1):**
   - Strictly enforces single-worker execution by default to avoid persistent profile lock collisions and duplicate submission races.
2. **Session Generation Cap (`MAX_GENERATIONS_PER_SESSION`, default = 10):**
   - Prevents an individual runner process from executing unbounded iterations.
3. **Daily Generation Cap (`MAX_DAILY_GENERATIONS`, default = 20):**
   - Queried atomically from SQLite (`repository.count_daily_generations()`).
   - Counts all `COMPLETED` and `GENERATING` jobs started within the current UTC date.
   - If the daily count reaches or exceeds the threshold, subsequent jobs are rejected with an explicit safety error before browser navigation occurs.

---

## Pre-Submission Approval & Audit Trail

When a prompt is submitted:
1. The system checks if Google Flow displays a credit confirmation or policy dialogue (`FlowSelectors.APPROVAL_PROMPT_CONTAINER`).
2. If `AUTO_CONFIRM_GENERATION=True`, it automatically clicks `Always approve` or `Approve` and captures the button text and timestamp in the audit proof.
3. The job's database record records:
   - `credit_cost_verified`: True if verified, False if estimated/unknown
   - `verified_credit_cost`: Actual token cost deducted (if disclosed by Flow)
   - `submission_confirmation`: JSON audit log containing submission timestamp, auto-approval status, and button evidence.
