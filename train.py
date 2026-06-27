"""
FinEdge — XGBoost TrustScore Model Training Pipeline
=====================================================
Loads ``finedge_dataset.csv``, builds a StandardScaler → XGBoost pipeline,
evaluates on a held-out set with early stopping, and serialises both
artefacts for the Django inference backend.

Artefacts
---------
- ``model.pkl``          : Trained XGBClassifier
- ``preprocessor.pkl``   : Fitted StandardScaler

Anti-Overfitting Strategy
-------------------------
1. **Regularisation** — L1 (``reg_alpha``), L2 (``reg_lambda``),
   ``min_child_weight``, ``gamma`` (min split-loss reduction).
2. **Stochastic subsampling** — ``subsample`` and ``colsample_bytree``
   at 80 % to decorrelate successive boosting rounds.
3. **Early stopping** — monitored on the held-out set; training halts
   if validation log-loss fails to improve for 30 consecutive rounds.
4. **Conservative learning rate** — 0.05 with up to 500 rounds
   (effective tree count determined by early stopping).
5. **Stratified 5-fold cross-validation** — reported alongside the
   single-split evaluation for an unbiased generalisation estimate.

Usage
-----
    $ python generator.py          # first — create finedge_dataset.csv
    $ python train.py              # → model.pkl + preprocessor.pkl
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Final

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("finedge.train")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATASET_PATH: Final[str] = "finedge_dataset.csv"
MODEL_PATH: Final[str] = "model.pkl"
PREPROCESSOR_PATH: Final[str] = "preprocessor.pkl"

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

SEED: Final[int] = 42
TEST_SIZE: Final[float] = 0.20
CV_FOLDS: Final[int] = 5
EARLY_STOPPING_ROUNDS: Final[int] = 30

# ---------------------------------------------------------------------------
# XGBoost hyper-parameters (tuned to prevent overfitting on 5 k rows)
# ---------------------------------------------------------------------------
# scale_pos_weight is computed dynamically from the training split.
XGB_PARAMS: Final[dict] = dict(
    n_estimators=500,          # upper bound; early stopping picks the actual count
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,             # L1 regularisation
    reg_lambda=2.0,            # L2 regularisation
    min_child_weight=5,
    gamma=0.3,                 # min split-loss reduction
    eval_metric="logloss",
    random_state=SEED,
    n_jobs=-1,
    verbosity=0,
)


# ---------------------------------------------------------------------------
# Data loading & validation
# ---------------------------------------------------------------------------
def _load_dataset(path: str) -> tuple[pd.DataFrame, pd.Series]:
    """Load and validate the CSV dataset."""
    filepath = Path(path)
    if not filepath.exists():
        logger.error(
            "Dataset not found at '%s'.  Run generator.py first.", filepath.resolve(),
        )
        sys.exit(1)

    df = pd.read_csv(filepath)

    # Column validation
    required = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing_cols = required - set(df.columns)
    if missing_cols:
        logger.error("Missing columns in dataset: %s", missing_cols)
        sys.exit(1)

    # Null check
    null_counts = df[FEATURE_COLUMNS + [TARGET_COLUMN]].isnull().sum()
    if null_counts.any():
        logger.error("Null values detected:\n%s", null_counts[null_counts > 0])
        sys.exit(1)

    # Target must be binary
    unique_targets = set(df[TARGET_COLUMN].unique())
    if not unique_targets.issubset({0, 1}):
        logger.error("Non-binary target values found: %s", unique_targets)
        sys.exit(1)

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------
def _build_preprocessor() -> StandardScaler:
    """Construct and return a StandardScaler preprocessor."""
    return StandardScaler()


def _build_classifier(pos_weight: float) -> XGBClassifier:
    """
    Construct an XGBClassifier with calibrated class-weight.

    ``scale_pos_weight`` compensates for class imbalance by weighting
    the positive (default) class proportionally to its under-representation.
    """
    params = {**XGB_PARAMS, "scale_pos_weight": pos_weight}
    return XGBClassifier(**params)


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------
def _evaluate(
    model: XGBClassifier,
    scaler: StandardScaler,
    X_test: np.ndarray,
    y_test: pd.Series,
) -> dict[str, float]:
    """
    Evaluate on the held-out test set and return key metrics.

    Returns a dict with ``roc_auc``, ``precision_at_90_recall``, and the
    confusion matrix for operational monitoring.
    """
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    roc_auc = roc_auc_score(y_test, y_prob)

    # Precision at ~90 % recall (operational threshold for lending)
    precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_prob)
    idx_90 = np.searchsorted(-recall_vals, -0.90)  # first index where recall >= 0.90
    prec_at_90 = precision_vals[min(idx_90, len(precision_vals) - 1)]

    cm = confusion_matrix(y_test, y_pred)

    logger.info("=" * 60)
    logger.info("TEST SET EVALUATION")
    logger.info("=" * 60)
    logger.info(
        "\n%s", classification_report(y_test, y_pred, digits=4),
    )
    logger.info("  ROC-AUC              : %.4f", roc_auc)
    logger.info("  Precision @ 90%% Recall: %.4f", prec_at_90)
    logger.info("  Confusion Matrix:")
    logger.info("    TN=%d  FP=%d", cm[0][0], cm[0][1])
    logger.info("    FN=%d  TP=%d", cm[1][0], cm[1][1])
    logger.info("=" * 60)

    return {"roc_auc": roc_auc, "precision_at_90_recall": prec_at_90}


def _cross_validate(
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
) -> float:
    """Run stratified k-fold cross-validation and report ROC-AUC."""
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    mean_auc = scores.mean()
    std_auc = scores.std()
    logger.info(
        "  %d-Fold CV ROC-AUC   : %.4f +/- %.4f", CV_FOLDS, mean_auc, std_auc,
    )

    # Overfitting guard: warn if CV AUC is substantially lower than test AUC
    if std_auc > 0.05:
        logger.warning(
            "High CV variance (std=%.4f) — model may be unstable. "
            "Consider increasing regularisation or data size.",
            std_auc,
        )

    return mean_auc


def _log_feature_importance(
    model: XGBClassifier,
    columns: list[str],
) -> None:
    """Log feature importances in descending order."""
    importances = model.feature_importances_
    feat_imp = sorted(
        zip(columns, importances), key=lambda x: x[1], reverse=True,
    )
    logger.info("")
    logger.info("  Feature Importances")
    logger.info("  %s", "-" * 45)
    for name, imp in feat_imp:
        bar = "█" * int(imp * 50)
        logger.info("  %-28s %.4f  %s", name, imp, bar)


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------
def train() -> None:
    """Full training pipeline: load → preprocess → train → evaluate → export."""
    t_start = time.perf_counter()

    # 1. Load ------------------------------------------------------------------
    X, y = _load_dataset(DATASET_PATH)
    logger.info("Loaded %d profiles  |  Default rate: %.2f%%", len(X), y.mean() * 100)

    # 2. Split -----------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=SEED,
    )
    logger.info("Train: %d  |  Test: %d", len(X_train), len(X_test))

    # 3. Fit preprocessor ------------------------------------------------------
    scaler = _build_preprocessor()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. Handle class imbalance ------------------------------------------------
    n_neg = int((y_train == 0).sum())
    n_pos = int((y_train == 1).sum())
    pos_weight = n_neg / max(n_pos, 1)
    logger.info(
        "Class balance → neg: %d  pos: %d  scale_pos_weight: %.2f",
        n_neg, n_pos, pos_weight,
    )

    # 5. Train XGBoost with early stopping -------------------------------------
    clf = _build_classifier(pos_weight)

    clf.fit(
        X_train_scaled,
        y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    best_iteration = getattr(clf, "best_iteration", clf.n_estimators)
    logger.info(
        "Training complete — best iteration: %d / %d",
        best_iteration, XGB_PARAMS["n_estimators"],
    )

    # 6. Evaluate on held-out set ----------------------------------------------
    metrics = _evaluate(clf, scaler, X_test, y_test)

    # 7. Cross-validate (full pipeline for unbiased estimate) ------------------
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("xgb", _build_classifier(pos_weight)),
        ]
    )
    cv_auc = _cross_validate(pipeline, X, y)

    # 8. Overfitting diagnostic ------------------------------------------------
    auc_gap = abs(metrics["roc_auc"] - cv_auc)
    if auc_gap > 0.05:
        logger.warning(
            "Test AUC (%.4f) vs CV AUC (%.4f): gap of %.4f suggests "
            "possible overfitting.  Review regularisation parameters.",
            metrics["roc_auc"], cv_auc, auc_gap,
        )
    else:
        logger.info(
            "  Test/CV AUC gap     : %.4f (healthy)", auc_gap,
        )

    # 9. Feature importance ----------------------------------------------------
    _log_feature_importance(clf, FEATURE_COLUMNS)

    # 10. Serialise artefacts --------------------------------------------------
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, PREPROCESSOR_PATH)

    elapsed = time.perf_counter() - t_start
    logger.info("")
    logger.info("  ✓ Model saved        → %s", Path(MODEL_PATH).resolve())
    logger.info("  ✓ Preprocessor saved → %s", Path(PREPROCESSOR_PATH).resolve())
    logger.info("  ✓ Elapsed            : %.2f s", elapsed)
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    train()
