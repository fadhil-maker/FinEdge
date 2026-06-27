"""
FinEdge — Dashboard Views (Platform Admin & Bank Officer)
==========================================================
Server-rendered Django template views for enterprise dashboards.

Dashboards
----------
1. **Admin Dashboard** (``/api/dashboard/admin/``)
   Platform owner view — total API revenue, per-tenant volume,
   velocity-lock fraud alerts.

2. **Officer Dashboard** (``/api/dashboard/officer/<tenant_code>/``)
   Partner bank view — tenant-scoped loan applications, TrustScores,
   decision badges, and Explainable AI reasoning.

Security
--------
- The Officer Dashboard enforces tenant isolation via ``tenant_code``
  URL parameter — only applications belonging to the resolved Bank
  are rendered.
- In production, these views should be protected by Django's
  ``@login_required`` and role-based permission decorators.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from typing import Any, Final

from django.db.models import Count, Sum, Q, F
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import (
    Bank,
    BillingLedger,
    LoanApplication,
    LoanApplicationStep,
    TrustScoreResult,
    FEATURE_COLUMNS,
    ContactMessage,
)
from .pipeline import (
    DECISION_BUREAU_APPROVED,
    DECISION_FALLBACK_AA,
    DECISION_ML_SCORED,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("finedge.dashboards")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Velocity lock threshold: > N applications from same device in 24 h
VELOCITY_LOCK_THRESHOLD: Final[int] = 5
VELOCITY_LOCK_WINDOW_HOURS: Final[int] = 24

# Explainable AI feature thresholds & labels
XAI_RULES: Final[list[dict[str, Any]]] = [
    {
        "feature": "utility_sms_count",
        "condition": lambda v: v > 30,
        "impact": "positive",
        "reason": "High UPI/banking SMS volume indicates active financial engagement",
        "icon": "📱",
    },
    {
        "feature": "utility_sms_count",
        "condition": lambda v: v == 0,
        "impact": "neutral",
        "reason": "Zero SMS — possible DND user; evaluated via Silent UPI path",
        "icon": "🔇",
    },
    {
        "feature": "financial_apps_count",
        "condition": lambda v: v >= 5,
        "impact": "positive",
        "reason": "High financial app diversity signals sophisticated money management",
        "icon": "💳",
    },
    {
        "feature": "financial_apps_count",
        "condition": lambda v: v <= 1,
        "impact": "negative",
        "reason": "Low financial app count — limited digital finance footprint",
        "icon": "⚠️",
    },
    {
        "feature": "device_age_days",
        "condition": lambda v: v > 365,
        "impact": "positive",
        "reason": "Device tenure > 1 year — stable ownership pattern",
        "icon": "📅",
    },
    {
        "feature": "device_age_days",
        "condition": lambda v: v < 14,
        "impact": "negative",
        "reason": "Thin file — device < 14 days old, insufficient behavioural signal",
        "icon": "🆕",
    },
    {
        "feature": "lifetime_emi_bounces",
        "condition": lambda v: v == 0,
        "impact": "positive",
        "reason": "Zero EMI bounces — excellent repayment discipline",
        "icon": "✅",
    },
    {
        "feature": "lifetime_emi_bounces",
        "condition": lambda v: v >= 3,
        "impact": "negative",
        "reason": "Multiple EMI bounces — repayment stress detected",
        "icon": "🔴",
    },
    {
        "feature": "average_monthly_balance",
        "condition": lambda v: v > 50000,
        "impact": "positive",
        "reason": "Strong average monthly balance (> ₹50,000) — healthy cash reserves",
        "icon": "💰",
    },
    {
        "feature": "average_monthly_balance",
        "condition": lambda v: v < 5000,
        "impact": "negative",
        "reason": "Low average balance (< ₹5,000) — limited savings buffer",
        "icon": "📉",
    },
    {
        "feature": "saved_contacts_ratio",
        "condition": lambda v: v > 0.5,
        "impact": "positive",
        "reason": "High saved-contacts ratio — strong social graph stability",
        "icon": "👥",
    },
    {
        "feature": "battery_deaths_weekly",
        "condition": lambda v: v >= 4,
        "impact": "negative",
        "reason": "Frequent battery drain — older/lower-quality device detected",
        "icon": "🔋",
    },
]


def _generate_xai_reasons(vector: dict[str, Any]) -> list[dict[str, str]]:
    """
    Generate Explainable AI reasons for a given feature vector.

    Evaluates each XAI rule against the vector and returns a list
    of matching explanations with impact polarity.
    """
    reasons = []
    for rule in XAI_RULES:
        feature = rule["feature"]
        value = vector.get(feature)
        if value is not None:
            try:
                if rule["condition"](float(value)):
                    reasons.append({
                        "icon": rule["icon"],
                        "impact": rule["impact"],
                        "reason": rule["reason"],
                        "feature": feature,
                        "value": value,
                    })
            except (TypeError, ValueError):
                continue
    return reasons


def _get_decision_display(trust_result: TrustScoreResult) -> dict[str, str]:
    """Map a TrustScoreResult to a human-readable decision badge."""
    vector = trust_result.mathematical_vector or {}
    step = trust_result.loan_application.current_step

    if step == LoanApplicationStep.FALLBACK_REVIEW:
        return {
            "label": "Pending Account Aggregator",
            "color": "amber",
            "bg": "bg-amber-500/10",
            "text": "text-amber-400",
            "border": "border-amber-500/20",
            "icon": "⏳",
        }

    score = trust_result.calculated_score
    if score is None:
        return {
            "label": "Pending Officer Review",
            "color": "slate",
            "bg": "bg-slate-500/10",
            "text": "text-slate-400",
            "border": "border-slate-500/20",
            "icon": "⏳",
        }

    # Infer decision from waterfall metadata
    # Bureau approvals have score >= 750 and no default_probability
    if score >= 750 and trust_result.default_probability is None:
        return {
            "label": "Approved via Bureau",
            "color": "blue",
            "bg": "bg-blue-500/10",
            "text": "text-blue-400",
            "border": "border-blue-500/20",
            "icon": "🏦",
        }

    # ML-scored
    if score >= 650:
        return {
            "label": "Approved via Edge-ML",
            "color": "green",
            "bg": "bg-emerald-500/10",
            "text": "text-emerald-400",
            "border": "border-emerald-500/20",
            "icon": "🤖",
        }

    return {
        "label": "Under Review",
        "color": "red",
        "bg": "bg-red-500/10",
        "text": "text-red-400",
        "border": "border-red-500/20",
        "icon": "🔍",
    }


def _detect_velocity_locks() -> list[dict[str, Any]]:
    """
    Detect velocity-lock (fraud) events.

    A velocity lock is triggered when the same device_hash_mask
    appears in more than VELOCITY_LOCK_THRESHOLD SDK sessions
    within the look-back window.
    """
    cutoff = timezone.now() - timedelta(hours=VELOCITY_LOCK_WINDOW_HOURS)

    from .models import SdkSession

    suspicious = (
        SdkSession.objects
        .filter(created_at__gte=cutoff)
        .values("device_hash_mask", "bank__tenant_code", "bank__name")
        .annotate(request_count=Count("id"))
        .filter(request_count__gt=VELOCITY_LOCK_THRESHOLD)
        .order_by("-request_count")
    )

    alerts = []
    for entry in suspicious:
        alerts.append({
            "device_hash": entry["device_hash_mask"][:16] + "…",
            "tenant_code": entry["bank__tenant_code"],
            "bank_name": entry["bank__name"],
            "request_count": entry["request_count"],
            "threshold": VELOCITY_LOCK_THRESHOLD,
            "window_hours": VELOCITY_LOCK_WINDOW_HOURS,
            "severity": "critical" if entry["request_count"] > VELOCITY_LOCK_THRESHOLD * 2 else "warning",
        })

    return alerts


# ═══════════════════════════════════════════════════════════════════════════
# Admin Dashboard (Platform Owner)
# ═══════════════════════════════════════════════════════════════════════════
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Platform admin dashboard — aggregate KPIs across all tenants.

    Context
    -------
    - total_revenue          : Sum of all BillingLedger charges.
    - total_applications     : Count of all LoanApplications.
    - total_tenants          : Count of active Banks.
    - avg_trust_score        : Average TrustScore across all results.
    - tenant_volumes         : Per-tenant API request counts + revenue.
    - velocity_alerts        : Detected velocity-lock fraud events.
    - recent_applications    : Latest 20 applications across all tenants.
    - score_distribution     : Score band breakdown for charts.
    """
    # ── KPI Metrics ───────────────────────────────────────────────────────
    total_revenue = (
        BillingLedger.objects.aggregate(total=Sum("computed_charge"))["total"]
        or Decimal("0.00")
    )

    total_applications = LoanApplication.objects.count()
    total_tenants = Bank.objects.filter(is_active=True).count()

    from django.db.models import Avg
    avg_score_result = TrustScoreResult.objects.aggregate(avg=Avg("calculated_score"))
    avg_trust_score = int(avg_score_result["avg"] or 0)

    thin_file_count = TrustScoreResult.objects.filter(is_thin_file=True).count()
    fallback_count = LoanApplication.objects.filter(
        current_step=LoanApplicationStep.FALLBACK_REVIEW,
    ).count()

    # ── Per-Tenant Volume Table ───────────────────────────────────────
    tenant_volumes = []
    for b in Bank.objects.filter(is_active=True).order_by('name'):
        app_count = b.loan_applications.count()
        rev_agg = b.billing_entries.aggregate(total=Sum("computed_charge"))
        revenue = rev_agg["total"] or Decimal("0.00")
        session_count = b.sdk_sessions.count()
        
        tenant_volumes.append({
            "name": b.name,
            "tenant_code": b.tenant_code,
            "app_count": app_count,
            "revenue": revenue,
            "session_count": session_count,
        })

    # ── Velocity Lock Alerts ──────────────────────────────────────────────
    velocity_alerts = _detect_velocity_locks()

    # ── Recent Applications ───────────────────────────────────────────────
    recent_applications = (
        LoanApplication.objects
        .select_related("bank", "trust_score")
        .order_by("-created_at")[:20]
    )

    # ── Score Distribution ────────────────────────────────────────────────
    score_bands = [
        {"label": "300–499 (High Risk)", "min": 300, "max": 499, "color": "red"},
        {"label": "500–649 (Fair)", "min": 500, "max": 649, "color": "amber"},
        {"label": "650–749 (Good)", "min": 650, "max": 749, "color": "cyan"},
        {"label": "750–900 (Excellent)", "min": 750, "max": 900, "color": "emerald"},
    ]
    for band in score_bands:
        band["count"] = TrustScoreResult.objects.filter(
            calculated_score__gte=band["min"],
            calculated_score__lte=band["max"],
        ).count()

    total_scored = sum(b["count"] for b in score_bands) or 1
    for band in score_bands:
        band["pct"] = round(band["count"] / total_scored * 100, 1)

    context = {
        "total_revenue": total_revenue,
        "total_applications": total_applications,
        "total_tenants": total_tenants,
        "avg_trust_score": avg_trust_score,
        "thin_file_count": thin_file_count,
        "fallback_count": fallback_count,
        "tenant_volumes": tenant_volumes,
        "velocity_alerts": velocity_alerts,
        "recent_applications": recent_applications,
        "score_bands": score_bands,
        "contact_messages": ContactMessage.objects.order_by("-created_at")[:20],
    }

    return render(request, "api_gateway/admin_dashboard.html", context)


# ═══════════════════════════════════════════════════════════════════════════
# Officer Dashboard (Partner Bank)
# ═══════════════════════════════════════════════════════════════════════════
def officer_dashboard(request: HttpRequest, tenant_code: str) -> HttpResponse:
    """
    Partner bank officer dashboard — tenant-scoped view.

    All queries are filtered through ``tenant_code`` to enforce
    Broken Object Level Authorization (BOLA) prevention.

    Context
    -------
    - bank                 : The resolved Bank instance.
    - applications         : LoanApplications with TrustScores + XAI reasons.
    - stats                : Tenant-level KPIs (total apps, avg score, etc.)
    """
    # ── Resolve Tenant ────────────────────────────────────────────────────
    try:
        bank = Bank.objects.get(tenant_code=tenant_code, is_active=True)
    except Bank.DoesNotExist:
        raise Http404(f"Bank with tenant_code '{tenant_code}' not found or inactive.")

    logger.info("Officer dashboard accessed for tenant: %s", tenant_code)

    # ── Tenant-Scoped Applications ────────────────────────────────────────
    applications_qs = (
        LoanApplication.tenant_objects.for_tenant(bank)
        .select_related("trust_score", "sdk_session")
        .order_by("-created_at")[:50]
    )

    # Enrich each application with decision badge + XAI reasons
    enriched_applications = []
    for app in applications_qs:
        trust = getattr(app, "trust_score", None)

        entry = {
            "id": app.id,
            "tracking_reference": app.tracking_reference,
            "current_step": app.get_current_step_display(),
            "current_step_raw": app.current_step,
            "created_at": app.created_at,
            "trust_score": None,
            "default_probability": None,
            "decision_badge": None,
            "xai_reasons": [],
            "mathematical_vector": None,
            "is_thin_file": False,
            "model_version": None,
        }

        if trust:
            entry["trust_score"] = trust.calculated_score
            entry["default_probability"] = trust.default_probability
            entry["is_thin_file"] = trust.is_thin_file
            entry["model_version"] = trust.model_version
            entry["mathematical_vector"] = trust.mathematical_vector
            entry["decision_badge"] = _get_decision_display(trust)
            entry["xai_reasons"] = _generate_xai_reasons(
                trust.mathematical_vector or {}
            )

        enriched_applications.append(entry)

    # ── Tenant KPIs ───────────────────────────────────────────────────────
    total_apps = LoanApplication.tenant_objects.for_tenant(bank).count()

    from django.db.models import Avg
    avg_score = (
        TrustScoreResult.objects
        .filter(loan_application__bank=bank)
        .aggregate(avg=Avg("calculated_score"))["avg"]
    )
    avg_score = int(avg_score or 0)

    approval_count = (
        LoanApplication.tenant_objects.for_tenant(bank)
        .filter(current_step=LoanApplicationStep.SCORE_COMPUTED)
        .count()
    )

    fallback_count = (
        LoanApplication.tenant_objects.for_tenant(bank)
        .filter(current_step=LoanApplicationStep.FALLBACK_REVIEW)
        .count()
    )

    tenant_revenue = (
        BillingLedger.tenant_objects.for_tenant(bank)
        .aggregate(total=Sum("computed_charge"))["total"]
        or Decimal("0.00")
    )

    thin_file_count = (
        TrustScoreResult.objects
        .filter(loan_application__bank=bank, is_thin_file=True)
        .count()
    )

    stats = {
        "total_apps": total_apps,
        "avg_score": avg_score,
        "approval_count": approval_count,
        "fallback_count": fallback_count,
        "tenant_revenue": tenant_revenue,
        "thin_file_count": thin_file_count,
    }

    context = {
        "bank": bank,
        "applications": enriched_applications,
        "stats": stats,
    }

    return render(request, "api_gateway/officer_dashboard.html", context)
