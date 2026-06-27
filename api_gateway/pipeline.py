"""
FinEdge — Underwriting Waterfall Pipeline
==========================================
Implements the three-step credit-decision waterfall that processes each
loan application submitted through the Edge SDK.

Waterfall Steps
---------------
1. **Bureau Check** (simulated) — If the applicant has a traditional
   bureau score > 750, approve immediately via the bureau path.
   This short-circuits the ML pipeline for established borrowers.

2. **Thin-File Guard** — If ``device_age_days < 14``, the device has
   insufficient behavioural signal.  Route to an Account Aggregator
   fallback for consent-based bank-statement analysis.

3. **XGBoost TrustScore** — Load the trained ``model.pkl`` and
   ``preprocessor.pkl``, run inference on the 7-feature mathematical
   vector, and scale the predicted default probability into a 300–900
   TrustScore.

Thread Safety
-------------
The ML artefacts are loaded once at module level (process startup) and
are read-only during inference — safe for concurrent WSGI workers.

Usage
-----
    from api_gateway.pipeline import evaluate_application

    result = evaluate_application({
        "device_age_days": 365,
        "utility_sms_count": 20,
        "battery_deaths_weekly": 1,
        "saved_contacts_ratio": 0.45,
        "financial_apps_count": 4,
        "average_monthly_balance": 25000.0,
        "lifetime_emi_bounces": 0,
    })
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import joblib
import numpy as np

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("finedge.pipeline")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FEATURE_COLUMNS: Final[list[str]] = [
    "device_age_days",
    "utility_sms_count",
    "battery_deaths_weekly",
    "saved_contacts_ratio",
    "financial_apps_count",
    "average_monthly_balance",
    "lifetime_emi_bounces",
]

# Waterfall decision codes
DECISION_BUREAU_APPROVED: Final[str] = "APPROVED_VIA_BUREAU"
DECISION_FALLBACK_AA: Final[str] = "FALLBACK_TO_ACCOUNT_AGGREGATOR"
DECISION_ML_SCORED: Final[str] = "ML_TRUSTSCORE_COMPUTED"

# Score range (analogous to traditional credit scores)
SCORE_MIN: Final[int] = 300
SCORE_MAX: Final[int] = 900

# Thresholds
BUREAU_APPROVAL_THRESHOLD: Final[int] = 750
THIN_FILE_MAX_DAYS: Final[int] = 14

# Simulated bureau score (in production, this calls an external bureau API)
SIMULATED_BUREAU_SCORE: Final[int] = 680

# ML artefact paths (relative to project root)
_BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH: Final[Path] = _BASE_DIR / "model.pkl"
PREPROCESSOR_PATH: Final[Path] = _BASE_DIR / "preprocessor.pkl"

# Model version tag (should match the version in train.py artefacts)
MODEL_VERSION: Final[str] = "v1.0.0"


# ---------------------------------------------------------------------------
# Waterfall result dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class WaterfallResult:
    """Immutable result object returned by the underwriting waterfall."""

    decision: str
    trust_score: int
    default_probability: float | None = None
    is_thin_file: bool = False
    model_version: str = MODEL_VERSION
    waterfall_step: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe dictionary."""
        return {
            "decision": self.decision,
            "trust_score": self.trust_score,
            "default_probability": self.default_probability,
            "is_thin_file": self.is_thin_file,
            "model_version": self.model_version,
            "waterfall_step": self.waterfall_step,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Lazy ML artefact loader (singleton pattern)
# ---------------------------------------------------------------------------
class _ModelRegistry:
    """
    Lazy-loading singleton for ML artefacts.

    Artefacts are loaded on first access and cached for the lifetime
    of the WSGI process.  This avoids:
    - Loading at import time (fails if artefacts don't exist yet).
    - Reloading on every request (wasteful).
    """

    _model = None
    _preprocessor = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Model artefact not found at {MODEL_PATH}.  "
                    "Run train.py to generate model.pkl."
                )
            cls._model = joblib.load(MODEL_PATH)
            logger.info("Loaded XGBoost model from %s", MODEL_PATH)
        return cls._model

    @classmethod
    def get_preprocessor(cls):
        if cls._preprocessor is None:
            if not PREPROCESSOR_PATH.exists():
                raise FileNotFoundError(
                    f"Preprocessor artefact not found at {PREPROCESSOR_PATH}.  "
                    "Run train.py to generate preprocessor.pkl."
                )
            cls._preprocessor = joblib.load(PREPROCESSOR_PATH)
            logger.info("Loaded StandardScaler from %s", PREPROCESSOR_PATH)
        return cls._preprocessor

    @classmethod
    def reset(cls):
        """Force-reload artefacts (used after hot-swapping models)."""
        cls._model = None
        cls._preprocessor = None
        logger.info("Model registry reset — artefacts will reload on next call.")


# ---------------------------------------------------------------------------
# Payload validation
# ---------------------------------------------------------------------------
def _validate_payload(payload: dict[str, Any]) -> dict[str, float]:
    """
    Validate and normalise the incoming feature vector.

    Raises ``ValueError`` with a descriptive message if any required
    feature is missing or has an invalid type.
    """
    validated: dict[str, float] = {}

    for col in FEATURE_COLUMNS:
        if col not in payload:
            raise ValueError(
                f"Missing required feature: '{col}'.  "
                f"Expected features: {FEATURE_COLUMNS}"
            )
        raw_value = payload[col]

        # Coerce to float (accepts int, float, and numeric strings)
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Feature '{col}' has invalid value '{raw_value}'.  "
                f"Expected a numeric type."
            ) from exc

        # NaN / Inf guard
        if not np.isfinite(value):
            raise ValueError(
                f"Feature '{col}' has non-finite value ({raw_value}).  "
                f"NaN and Inf are not permitted."
            )

        validated[col] = value

    return validated


# ---------------------------------------------------------------------------
# Waterfall step implementations
# ---------------------------------------------------------------------------
def _step_1_bureau_check(
    payload: dict[str, float],
    bureau_score: int = SIMULATED_BUREAU_SCORE,
) -> WaterfallResult | None:
    """
    Step 1 — Traditional Bureau Check (simulated).

    In production this would call an external credit-bureau API (e.g.
    CIBIL / Experian India).  For now, we use a simulated score.

    If the bureau score exceeds the threshold (750), the applicant is
    approved immediately without needing the ML pipeline.
    """
    logger.info(
        "Waterfall Step 1: Bureau check (simulated score=%d, threshold=%d)",
        bureau_score, BUREAU_APPROVAL_THRESHOLD,
    )

    if bureau_score > BUREAU_APPROVAL_THRESHOLD:
        # Map bureau score to TrustScore range (750-900 bureau → 750-900 trust)
        trust_score = min(bureau_score, SCORE_MAX)
        logger.info(
            "Step 1 PASS: Bureau score %d > %d → %s",
            bureau_score, BUREAU_APPROVAL_THRESHOLD, DECISION_BUREAU_APPROVED,
        )
        return WaterfallResult(
            decision=DECISION_BUREAU_APPROVED,
            trust_score=trust_score,
            default_probability=None,
            is_thin_file=False,
            waterfall_step=1,
            metadata={"bureau_score": bureau_score},
        )

    logger.info("Step 1 SKIP: Bureau score %d ≤ %d → proceed to Step 2", bureau_score, BUREAU_APPROVAL_THRESHOLD)
    return None


def _step_2_thin_file_guard(
    payload: dict[str, float],
) -> WaterfallResult | None:
    """
    Step 2 — Thin-File Protection.

    If ``device_age_days < 14``, the device lacks sufficient behavioural
    signal for reliable ML scoring.  Route to the Account Aggregator
    fallback (consent-based bank-statement analysis).
    """
    device_age = int(payload["device_age_days"])
    logger.info(
        "Waterfall Step 2: Thin-file guard (device_age=%d, threshold=%d)",
        device_age, THIN_FILE_MAX_DAYS,
    )

    if device_age < THIN_FILE_MAX_DAYS:
        logger.warning(
            "Step 2 TRIGGER: device_age_days=%d < %d → %s",
            device_age, THIN_FILE_MAX_DAYS, DECISION_FALLBACK_AA,
        )
        return WaterfallResult(
            decision=DECISION_FALLBACK_AA,
            trust_score=SCORE_MIN,  # Assign floor score for thin files
            default_probability=None,
            is_thin_file=True,
            waterfall_step=2,
            metadata={"device_age_days": device_age, "reason": "insufficient_device_history"},
        )

    logger.info("Step 2 PASS: device_age=%d ≥ %d → proceed to Step 3", device_age, THIN_FILE_MAX_DAYS)
    return None


def _step_3_ml_inference(
    payload: dict[str, float],
) -> WaterfallResult:
    """
    Step 3 — XGBoost TrustScore Inference.

    Load the trained model and preprocessor, construct the feature
    array in the exact column order used during training, run inference,
    and scale the predicted default probability to the 300–900 range.

    Scaling formula::

        trust_score = 900 - (probability_of_default × 600)

    This maps p=0.0 → 900 (best) and p=1.0 → 300 (worst).
    """
    logger.info("Waterfall Step 3: XGBoost ML inference")

    model = _ModelRegistry.get_model()
    preprocessor = _ModelRegistry.get_preprocessor()

    # Construct feature array in training column order
    feature_array = np.array(
        [[payload[col] for col in FEATURE_COLUMNS]],
        dtype=np.float64,
    )

    # Scale features
    feature_scaled = preprocessor.transform(feature_array)

    # Predict
    default_prob = float(model.predict_proba(feature_scaled)[0, 1])

    # Scale probability → TrustScore (300–900)
    raw_score = SCORE_MAX - int(default_prob * (SCORE_MAX - SCORE_MIN))
    trust_score = max(SCORE_MIN, min(SCORE_MAX, raw_score))

    logger.info(
        "Step 3 COMPLETE: p(default)=%.4f → TrustScore=%d",
        default_prob, trust_score,
    )

    return WaterfallResult(
        decision=DECISION_ML_SCORED,
        trust_score=trust_score,
        default_probability=round(default_prob, 6),
        is_thin_file=False,
        model_version=MODEL_VERSION,
        waterfall_step=3,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Public API — Waterfall Orchestrator
# ---------------------------------------------------------------------------
def evaluate_application(
    payload: dict[str, Any],
    bureau_score: int = SIMULATED_BUREAU_SCORE,
) -> WaterfallResult:
    """
    Execute the FinEdge underwriting waterfall on a mathematical vector.

    Parameters
    ----------
    payload : dict
        JSON-decoded feature vector from the Edge SDK.  Must contain
        all keys in ``FEATURE_COLUMNS``.
    bureau_score : int, optional
        Simulated traditional bureau score (default: 680).  In production,
        this would be fetched from an external API.

    Returns
    -------
    WaterfallResult
        Immutable result with the decision, TrustScore, and metadata.

    Raises
    ------
    ValueError
        If the payload is missing features or contains invalid values.
    FileNotFoundError
        If the ML artefacts (model.pkl / preprocessor.pkl) are missing.
    """
    logger.info("=" * 60)
    logger.info("WATERFALL START — evaluating application")
    logger.info("=" * 60)

    # Validate & normalise payload
    validated_payload = _validate_payload(payload)

    # Step 1: Bureau check
    result = _step_1_bureau_check(validated_payload, bureau_score=bureau_score)
    if result is not None:
        logger.info("WATERFALL COMPLETE at Step 1: %s", result.decision)
        return result

    # Step 2: Thin-file guard
    result = _step_2_thin_file_guard(validated_payload)
    if result is not None:
        logger.info("WATERFALL COMPLETE at Step 2: %s", result.decision)
        return result

    # Step 3: ML inference
    result = _step_3_ml_inference(validated_payload)
    logger.info("WATERFALL COMPLETE at Step 3: %s (score=%d)", result.decision, result.trust_score)
    return result
