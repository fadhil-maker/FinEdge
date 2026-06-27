"""
FinEdge — Synthetic Alternative Credit Scoring Dataset Generator
================================================================
Generates 5,000 privacy-preserving smartphone-metadata profiles with
deterministic edge-case masking and exports to ``finedge_dataset.csv``.

Architecture
------------
On-device, the Edge SDK extracts mathematical metadata from the smartphone
(app usage, SMS patterns, battery telemetry, contacts graph).  Raw data is
purged locally; only the resulting integer / float vector is transmitted.

This script synthesises realistic training data that mirrors those vectors.

Edge Cases
----------
1. **Silent UPI User** — ``utility_sms_count == 0`` AND
   ``financial_apps_count > 2`` → forced ``loan_default_status = 0``
   (low risk).  Rationale: zero SMS with many finance apps indicates a
   sophisticated digital-finance user who has disabled SMS permissions.

2. **Thin File** — ``device_age_days < 14`` → randomised high-risk
   assignment (≈ 70 % default).  Rationale: insufficient behavioural signal;
   the downstream inference API should trigger a manual-review fallback.

Usage
-----
    $ python generator.py                 # → finedge_dataset.csv (5 000 rows)
    $ python generator.py --profiles 10000 --output custom.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("finedge.generator")

# ---------------------------------------------------------------------------
# Feature specification (single source of truth)
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
TARGET_COLUMN: Final[str] = "loan_default_status"


# ---------------------------------------------------------------------------
# Configuration (dataclass — easy to serialise / override)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GeneratorConfig:
    """Immutable configuration for the synthetic-data generator."""

    n_profiles: int = 5_000
    seed: int = 42
    output_path: str = "finedge_dataset.csv"

    # Edge-case thresholds
    thin_file_max_days: int = 14
    thin_file_default_prob: float = 0.70
    silent_upi_min_apps: int = 2

    # Base default rate calibration
    base_default_rate: float = 0.18

    # Distribution parameters
    device_age_gamma_shape: float = 2.0
    device_age_gamma_scale: float = 180.0
    device_age_max: int = 1825          # ~5 years
    sms_zero_prob: float = 0.30         # ~30 % have zero SMS
    sms_poisson_lambda: float = 25.0
    battery_poisson_lambda: float = 1.2
    battery_max: int = 15
    contacts_beta_a: float = 2.0
    contacts_beta_b: float = 5.0
    finance_apps_poisson_lambda: float = 3.0
    finance_apps_max: int = 20
    balance_lognormal_mean: float = 9.0
    balance_lognormal_sigma: float = 1.2
    balance_max: float = 5_000_000.0
    emi_bounces_poisson_lambda: float = 0.8
    emi_bounces_max: int = 30


# ---------------------------------------------------------------------------
# Feature generation
# ---------------------------------------------------------------------------
def _generate_raw_features(
    rng: np.random.Generator,
    cfg: GeneratorConfig,
) -> pd.DataFrame:
    """
    Sample raw feature vectors from realistic marginal distributions.

    Each feature is drawn independently from a parameterised distribution
    chosen to approximate the real-world marginals observed in Indian
    smartphone-lending populations.
    """
    n = cfg.n_profiles

    data = pd.DataFrame(
        {
            # Device tenure in days (0 – 1 825 ≈ 5 years), right-skewed
            "device_age_days": (
                rng.gamma(shape=cfg.device_age_gamma_shape,
                          scale=cfg.device_age_gamma_scale, size=n)
                .clip(0, cfg.device_age_max)
                .astype(int)
            ),
            # Count of utility / transactional SMS received per month
            # ~30 % of users have zero (feature phones / DND)
            "utility_sms_count": np.where(
                rng.random(n) < cfg.sms_zero_prob,
                0,
                rng.poisson(lam=cfg.sms_poisson_lambda, size=n),
            ),
            # Weekly battery-drain-to-zero events (proxy for phone quality)
            "battery_deaths_weekly": (
                rng.poisson(lam=cfg.battery_poisson_lambda, size=n)
                .clip(0, cfg.battery_max)
            ),
            # Ratio of saved contacts to total call-log entries [0, 1]
            "saved_contacts_ratio": (
                rng.beta(a=cfg.contacts_beta_a, b=cfg.contacts_beta_b, size=n)
                .round(4)
            ),
            # Number of finance-category apps installed
            "financial_apps_count": (
                rng.poisson(lam=cfg.finance_apps_poisson_lambda, size=n)
                .clip(0, cfg.finance_apps_max)
            ),
            # Avg monthly bank-account balance (INR), log-normal
            "average_monthly_balance": (
                rng.lognormal(mean=cfg.balance_lognormal_mean,
                              sigma=cfg.balance_lognormal_sigma, size=n)
                .clip(0, cfg.balance_max)
                .round(2)
            ),
            # Lifetime EMI bounce count
            "lifetime_emi_bounces": (
                rng.poisson(lam=cfg.emi_bounces_poisson_lambda, size=n)
                .clip(0, cfg.emi_bounces_max)
            ),
        }
    )
    return data


# ---------------------------------------------------------------------------
# Target derivation
# ---------------------------------------------------------------------------
def _compute_base_default_probability(df: pd.DataFrame) -> np.ndarray:
    """
    Derive a latent default probability from a linear combination of
    features passed through a sigmoid, calibrated so the marginal default
    rate is approximately ``BASE_DEFAULT_RATE`` (~18 %).

    The coefficients are hand-tuned to produce realistic separation
    between defaulters and non-defaulters in the feature space.
    """
    z = (
        -2.5
        + 0.003 * (730 - df["device_age_days"].values)       # newer → riskier
        + 0.02  * (30  - df["utility_sms_count"].values)      # fewer SMS → riskier
        + 0.15  * df["battery_deaths_weekly"].values           # more deaths → riskier
        - 1.0   * df["saved_contacts_ratio"].values            # lower ratio → riskier
        - 0.05  * df["financial_apps_count"].values            # fewer apps → riskier
        - 0.00001 * df["average_monthly_balance"].values       # lower balance → riskier
        + 0.30  * df["lifetime_emi_bounces"].values            # more bounces → riskier
    )
    prob = 1.0 / (1.0 + np.exp(-z))
    return prob


# ---------------------------------------------------------------------------
# Edge-case masking
# ---------------------------------------------------------------------------
def _apply_edge_cases(
    df: pd.DataFrame,
    rng: np.random.Generator,
    cfg: GeneratorConfig,
) -> pd.DataFrame:
    """
    Mutate ``loan_default_status`` according to the two business edge cases.

    **Edge Case 1 — Silent UPI User**
        Profiles with zero SMS *but* more than 2 financial apps are
        sophisticated digital-finance users.  Force label = 0.

    **Edge Case 2 — Thin File**
        Devices younger than 14 days carry insufficient behavioural signal.
        Re-randomise their label with a high default probability
        (≈ 70 %) to trigger the downstream fallback route.

    Both masks are applied in order; if a profile satisfies *both*
    conditions, the Thin File override takes precedence (applied second).
    """
    df = df.copy()

    # --- Edge Case 1: Silent UPI User → low risk -----------------------------
    silent_upi_mask = (
        (df["utility_sms_count"] == 0)
        & (df["financial_apps_count"] > cfg.silent_upi_min_apps)
    )
    n_silent = silent_upi_mask.sum()
    df.loc[silent_upi_mask, TARGET_COLUMN] = 0
    logger.info(
        "Edge Case 1 (Silent UPI): %d profiles masked as low-risk", n_silent,
    )

    # --- Edge Case 2: Thin File → randomised high risk -----------------------
    thin_file_mask = df["device_age_days"] < cfg.thin_file_max_days
    n_thin = thin_file_mask.sum()
    df.loc[thin_file_mask, TARGET_COLUMN] = (
        rng.random(n_thin) < cfg.thin_file_default_prob
    ).astype(int)
    logger.info(
        "Edge Case 2 (Thin File): %d profiles re-randomised (p=%.0f%%)",
        n_thin, cfg.thin_file_default_prob * 100,
    )

    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _validate_dataset(df: pd.DataFrame, cfg: GeneratorConfig) -> None:
    """Run sanity checks on the generated dataset."""
    assert len(df) == cfg.n_profiles, (
        f"Row count mismatch: expected {cfg.n_profiles}, got {len(df)}"
    )
    assert set(FEATURE_COLUMNS + [TARGET_COLUMN]).issubset(df.columns), (
        "Missing columns in generated DataFrame"
    )

    # No nulls
    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(f"Null values detected:\n{null_counts[null_counts > 0]}")

    # Target must be binary
    unique_targets = set(df[TARGET_COLUMN].unique())
    assert unique_targets.issubset({0, 1}), (
        f"Non-binary target values found: {unique_targets}"
    )

    # Default rate within a plausible band (5 %–50 %)
    default_rate = df[TARGET_COLUMN].mean()
    assert 0.05 <= default_rate <= 0.50, (
        f"Default rate {default_rate:.2%} is outside plausible range [5 %, 50 %]"
    )

    # Feature-level bounds
    assert (df["device_age_days"] >= 0).all()
    assert (df["saved_contacts_ratio"].between(0, 1)).all()
    assert (df["average_monthly_balance"] >= 0).all()

    logger.info("✓ All validation checks passed")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_dataset(cfg: GeneratorConfig | None = None) -> pd.DataFrame:
    """End-to-end dataset generation pipeline."""
    if cfg is None:
        cfg = GeneratorConfig()

    rng = np.random.default_rng(cfg.seed)

    # 1. Sample raw features
    logger.info("Generating %d synthetic profiles (seed=%d) …", cfg.n_profiles, cfg.seed)
    df = _generate_raw_features(rng, cfg)

    # 2. Derive base default probabilities & sample binary target
    prob = _compute_base_default_probability(df)
    df[TARGET_COLUMN] = (rng.random(cfg.n_profiles) < prob).astype(int)
    logger.info(
        "Base default rate (pre-masking): %.2f%%", df[TARGET_COLUMN].mean() * 100,
    )

    # 3. Apply deterministic edge-case overrides
    df = _apply_edge_cases(df, rng, cfg)

    # 4. Validate
    _validate_dataset(df, cfg)

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FinEdge — Synthetic Alternative Credit Scoring Dataset Generator",
    )
    parser.add_argument(
        "--profiles", type=int, default=5_000,
        help="Number of synthetic profiles to generate (default: 5000)",
    )
    parser.add_argument(
        "--output", type=str, default="finedge_dataset.csv",
        help="Output CSV path (default: finedge_dataset.csv)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    args = _parse_args()
    config = GeneratorConfig(
        n_profiles=args.profiles,
        output_path=args.output,
        seed=args.seed,
    )

    t_start = time.perf_counter()
    dataset = generate_dataset(config)
    dataset.to_csv(config.output_path, index=False)
    elapsed = time.perf_counter() - t_start

    # ---- Summary statistics -----------------------------------------------
    n_default = dataset[TARGET_COLUMN].sum()
    n_silent = (
        (dataset["utility_sms_count"] == 0)
        & (dataset["financial_apps_count"] > config.silent_upi_min_apps)
    ).sum()
    n_thin = (dataset["device_age_days"] < config.thin_file_max_days).sum()

    logger.info("=" * 60)
    logger.info("FinEdge — Synthetic Dataset Generated")
    logger.info("=" * 60)
    logger.info("  Total profiles       : %6d", len(dataset))
    logger.info("  Default rate         : %8.2f%%", n_default / len(dataset) * 100)
    logger.info("  Silent-UPI overrides : %6d", n_silent)
    logger.info("  Thin-file overrides  : %6d", n_thin)
    logger.info("  Output               : %s", Path(config.output_path).resolve())
    logger.info("  Elapsed              : %.2f s", elapsed)
    logger.info("=" * 60)
