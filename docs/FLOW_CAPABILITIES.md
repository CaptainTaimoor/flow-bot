# Google Flow Live Capability Discovery & Model Truthfulness

## Overview
Google Flow (`https://flow.google.com/`) is a dynamic, continuously updating web studio application for AI video, image generation, and scene building. Unlike fixed REST APIs with static versioned schemas, Flow's available models, aspect ratios, credit balances, and operational limits can vary by user tier (Standard vs Pro), subscription status, region, and live experiments.

To prevent hallucinations, credit loss, and fragile automation breakage, this system enforces **truthful DOM-driven capability discovery** directly against the active browser session.

---

## Core Invariants

1. **Zero Hallucinated Models or IDs:**
   - The automation system never invents model identifiers (e.g. `veo-v3-ultra-pro`, `veo-2-turbo`).
   - Discovered models are extracted directly from the live prompt bar pill (`flow-model-select button`, `[aria-label*='model' i]`) and its associated Angular/Material options menu (`[role='menuitem']`, `flow-select-option`).
   - If DOM extraction is unverified, fallback defaults are explicitly annotated with `model_source="fallback"`.

2. **Truthful Credit Balances:**
   - Credit balances are never hard-coded or fabricated.
   - Balances are inspected from Flow's live user header chip (`.flow-user-tier-chip`, `flow-header-user-icon`) and credit containers.
   - If Flow does not expose a numerical balance in the DOM, the system truthfully returns `credit_status="UNKNOWN"` and `credit_balance=None`.

3. **No Silent Downgrades or Mutations:**
   - When a user submits a job requesting a specific model, orientation, or output count, the system records both:
     - `requested_model`, `requested_orientation`, `requested_duration`, `requested_output_count`
     - `effective_model`, `effective_orientation`, `effective_duration`, `effective_output_count`
   - If a requested parameter cannot be selected in Flow's live UI, the mismatch is logged, audited, and preserved in the job record.

---

## Discovery Pipeline (`src/flow/capability_detection.py`)

The capability detection engine executes the following sequential steps:

1. **Modal & Announcement Dismissal:**
   - Inspects and closes transient dialogues (`Got it`, `Dismiss`, `I understand`) and gallery hero banners (`Start Creating`, close button `x`).
2. **Authentication Verification:**
   - Checks whether the user is logged into Google (`AUTHENTICATED`, `NOT_AUTHENTICATED`, `CHALLENGE_REQUIRED`, `UNKNOWN`).
3. **Workspace Surface Detection:**
   - Verifies presence of the studio prompt input (`.ProseMirror`, `div[contenteditable='true']`).
   - Inspects for the presence of the agent panel (`flow-agent-panel`, `flow-chat-view`).
4. **Live Model Discovery:**
   - Queries the active model pill on the prompt bar.
   - If clickable, opens the model selection menu, enumerates all live options, and closes the menu cleanly.
5. **Credit Inspection:**
   - Parses the header badge and credit indicators for numerical token counters.

---

## Data Schema (`FlowCapabilities`)

```json
{
  "flow_available": true,
  "authenticated": true,
  "auth_state": "AUTHENTICATED",
  "active_model": "Veo 2",
  "models_available": ["Veo 2"],
  "model_source": "live_ui",
  "credit_status": "UNKNOWN",
  "credit_balance": null,
  "credit_cost_per_job": null,
  "standard_generation": true,
  "agent_available": true,
  "last_checked": "2026-09-25T05:30:00Z"
}
```

---

## Diagnostics API
Clients can query the truthful capabilities at any time via:
- `GET /capabilities`
- `GET /diagnostics`
- Real-time SSE updates via `GET /status`
