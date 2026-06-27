"""
FinEdge — Django Database Schema (Multi-Tenant Credit Scoring Backend)
======================================================================
Production-grade, multi-tenant data models for the FinEdge
Privacy-Preserving Edge-ML Alternative Credit Scoring Platform.

Architecture
------------
Every row is scoped to a **Bank** (tenant).  A custom ``TenantManager``
enforces mandatory tenant filtering at the ORM layer, preventing
Broken Object Level Authorization (BOLA / IDOR) vulnerabilities.

Security Design
---------------
- **UUID primary keys** on every model — eliminates sequential-ID
  enumeration attacks.
- **PROTECT on all FK deletes** — prevents accidental cascade deletion
  of financial records (regulatory requirement).
- **device_hash_mask** stores only a one-way hash of device identifiers
  so raw device IDs never touch the backend (zero-knowledge principle).
- **hashed_key** in ``ApiCredential`` stores HMAC-SHA256 digests; the
  plaintext API key is shown exactly once at provisioning time.

Models
------
1. ``Bank``              — Tenant (partner bank / NBFC).
2. ``ApiCredential``     — Per-tenant API key (hashed).
3. ``SdkSession``        — Edge SDK session envelope.
4. ``LoanApplication``   — Loan file progressing through the waterfall.
5. ``TrustScoreResult``  — ML inference output + raw feature vector.
6. ``BillingLedger``     — Per-API-call metered billing record.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Final

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Feature vector field names (single source of truth, shared with train.py)
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


# ═══════════════════════════════════════════════════════════════════════════
# Custom Multi-Tenant Manager (BOLA Prevention)
# ═══════════════════════════════════════════════════════════════════════════
class TenantManager(models.Manager):
    """
    Custom manager that enforces tenant-scoped queries.

    Usage
    -----
        # Always pass the requesting tenant to prevent cross-tenant leaks:
        LoanApplication.tenant_objects.for_tenant(bank_instance).filter(...)

        # The default `objects` manager is left intact for admin / migration
        # compatibility, but application code MUST use `tenant_objects`.

    Why a manager and not middleware?
    ---------------------------------
    Middleware-based tenant filtering is fragile — a single missed view
    leaks data.  A manager-level guard makes the isolation explicit at
    every query site and is auditable in code review.
    """

    def for_tenant(self, bank: "Bank") -> models.QuerySet:
        """Return a queryset filtered to the given tenant (Bank)."""
        return self.get_queryset().filter(bank=bank)


# ═══════════════════════════════════════════════════════════════════════════
# Abstract base with UUID PK
# ═══════════════════════════════════════════════════════════════════════════
class UUIDBaseModel(models.Model):
    """
    Abstract base providing a non-sequential UUID primary key and
    standard timestamp fields.

    Every concrete FinEdge model inherits from this to guarantee:
    - No auto-increment ID enumeration attacks.
    - Consistent ``created_at`` / ``updated_at`` audit columns.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Immutable UUID v4 primary key.",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Row creation timestamp (UTC).",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification timestamp (UTC).",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Bank (Tenant)
# ═══════════════════════════════════════════════════════════════════════════
class Bank(UUIDBaseModel):
    """
    A partner bank or NBFC onboarded onto the FinEdge platform.

    Each Bank is an isolated tenant — all downstream data (sessions,
    applications, scores, billing) is scoped through FK relationships
    back to this model.
    """

    name = models.CharField(
        max_length=255,
        help_text="Legal entity name of the bank / NBFC.",
    )
    tenant_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=(
            "Short, URL-safe code identifying the tenant "
            "(e.g. 'hdfc', 'axis_nbfc').  Used in API routing."
        ),
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Soft-disable flag.  Inactive tenants cannot submit new sessions.",
    )

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_bank"
        verbose_name = "Bank"
        verbose_name_plural = "Banks"

    def __str__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"{self.name} [{self.tenant_code}] ({status})"


# ═══════════════════════════════════════════════════════════════════════════
# 2. ApiCredential
# ═══════════════════════════════════════════════════════════════════════════
class ApiCredential(UUIDBaseModel):
    """
    Per-tenant API credential.

    The plaintext key is displayed exactly once during provisioning.
    Only the HMAC-SHA256 hash is persisted — the backend never stores
    or logs raw keys.
    """

    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name="api_credentials",
        help_text="Owning tenant.",
    )
    hashed_key = models.CharField(
        max_length=128,
        unique=True,
        help_text="HMAC-SHA256 digest of the API key (hex-encoded, 64 chars).",
    )
    label = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Human-readable label (e.g. 'production', 'staging').",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Revoke a credential without deleting the audit trail.",
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the most recent successful authentication.",
    )

    # Managers
    objects = models.Manager()
    tenant_objects = TenantManager()

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_api_credential"
        verbose_name = "API Credential"
        verbose_name_plural = "API Credentials"

    def __str__(self) -> str:
        return f"Credential [{self.label or 'unlabelled'}] → {self.bank.tenant_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 3. SdkSession
# ═══════════════════════════════════════════════════════════════════════════
class SdkSession(UUIDBaseModel):
    """
    Edge SDK session envelope.

    Each time the smartphone SDK performs a metadata extraction, a
    session is created.  ``device_hash_mask`` is a one-way SHA-256
    hash of the device's hardware identifiers — raw identifiers
    are purged on-device before transmission.
    """

    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name="sdk_sessions",
        help_text="Tenant that owns this session.",
    )
    device_hash_mask = models.CharField(
        max_length=128,
        db_index=True,
        help_text=(
            "SHA-256 hash of the device hardware identifiers.  "
            "Used for session deduplication without storing PII."
        ),
    )

    # Managers
    objects = models.Manager()
    tenant_objects = TenantManager()

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_sdk_session"
        verbose_name = "SDK Session"
        verbose_name_plural = "SDK Sessions"

    def __str__(self) -> str:
        mask_short = self.device_hash_mask[:12] + "…"
        return f"Session {self.id!s:.8} | device={mask_short}"


# ═══════════════════════════════════════════════════════════════════════════
# 4. LoanApplication
# ═══════════════════════════════════════════════════════════════════════════
class LoanApplicationStep(models.TextChoices):
    """Enumeration of waterfall steps a loan application progresses through."""

    SDK_RECEIVED      = "sdk_received",      "SDK Data Received"
    VECTOR_VALIDATED  = "vector_validated",   "Vector Validated"
    SCORE_COMPUTED    = "score_computed",     "TrustScore Computed"
    DECISION_RENDERED = "decision_rendered",  "Decision Rendered"
    FALLBACK_REVIEW   = "fallback_review",   "Fallback Manual Review"
    COMPLETED         = "completed",         "Completed"
    REJECTED          = "rejected",          "Rejected"
    ERROR             = "error",             "Processing Error"


class LoanApplication(UUIDBaseModel):
    """
    A loan file progressing through the FinEdge scoring waterfall.

    ``current_step`` tracks the application's position in the waterfall
    pipeline (receive → validate → score → decide).  Thin-file profiles
    are routed to ``FALLBACK_REVIEW``.
    """

    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name="loan_applications",
        help_text="Tenant that submitted this application.",
    )
    sdk_session = models.ForeignKey(
        SdkSession,
        on_delete=models.PROTECT,
        related_name="loan_applications",
        help_text="SDK session that produced the feature vector.",
    )
    tracking_reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=(
            "Client-supplied idempotency / tracking reference "
            "(e.g. partner's internal loan-application ID)."
        ),
    )
    current_step = models.CharField(
        max_length=50,
        choices=LoanApplicationStep.choices,
        default=LoanApplicationStep.SDK_RECEIVED,
        help_text="Current state in the underwriting pipeline.",
    )
    requested_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("2000.00"),
        help_text="Requested loan amount (defaulting to Mini Loan size)."
    )
    cibil_score = models.IntegerField(
        default=-1,
        help_text="Traditional CIBIL score (-1 means New to Credit)."
    )
    aa_status = models.CharField(
        max_length=20, default="pending",
        help_text="Account Aggregator status (e.g. pending, completed)."
    )

    # Managers
    objects = models.Manager()
    tenant_objects = TenantManager()

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_loan_application"
        verbose_name = "Loan Application"
        verbose_name_plural = "Loan Applications"
        constraints = [
            models.UniqueConstraint(
                fields=["bank", "tracking_reference"],
                name="uq_bank_tracking_ref",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Application {self.tracking_reference} "
            f"[{self.get_current_step_display()}] → {self.bank.tenant_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 5. TrustScoreResult
# ═══════════════════════════════════════════════════════════════════════════
class TrustScoreResult(UUIDBaseModel):
    """
    ML inference output for a single loan application.

    ``mathematical_vector`` stores the 7-feature JSON payload extracted
    by the Edge SDK.  ``calculated_score`` is the XGBoost-derived
    TrustScore (300–900 scale, analogous to a traditional credit score).
    """

    loan_application = models.OneToOneField(
        LoanApplication,
        on_delete=models.PROTECT,
        related_name="trust_score",
        help_text="The loan application this score belongs to.",
    )
    mathematical_vector = models.JSONField(
        help_text=(
            "Raw feature vector from the Edge SDK.  "
            "Schema: {device_age_days, utility_sms_count, "
            "battery_deaths_weekly, saved_contacts_ratio, "
            "financial_apps_count, average_monthly_balance, "
            "lifetime_emi_bounces}."
        ),
    )
    calculated_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(300),
            MaxValueValidator(900),
        ],
        help_text="XGBoost-derived TrustScore (300–900).",
    )
    default_probability = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0),
        ],
        help_text="Model-predicted probability of default [0.0, 1.0].",
    )
    model_version = models.CharField(
        max_length=50,
        default="v1.0.0",
        help_text="Semantic version of the XGBoost model used for inference.",
    )
    is_thin_file = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "True if device_age_days < 14 — triggers the fallback "
            "manual-review route."
        ),
    )

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_trust_score_result"
        verbose_name = "TrustScore Result"
        verbose_name_plural = "TrustScore Results"

    def __str__(self) -> str:
        thin = " [THIN FILE]" if self.is_thin_file else ""
        return (
            f"Score {self.calculated_score}{thin} → "
            f"{self.loan_application.tracking_reference}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 6. BillingLedger
# ═══════════════════════════════════════════════════════════════════════════
class BillingLedger(UUIDBaseModel):
    """
    Per-API-call metered billing record.

    Each successful TrustScore computation generates a ledger entry.
    ``processing_cycle_stamp`` groups entries for monthly invoicing
    (format: ``YYYY-MM``).
    """

    bank = models.ForeignKey(
        Bank,
        on_delete=models.PROTECT,
        related_name="billing_entries",
        help_text="Tenant being billed.",
    )
    computed_charge = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.0000"),
        help_text="Charge for this API call (INR).",
    )
    processing_cycle_stamp = models.CharField(
        max_length=7,
        db_index=True,
        help_text="Billing cycle identifier (YYYY-MM format, e.g. '2026-06').",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Human-readable billing note (e.g. 'TrustScore computation').",
    )

    # Managers
    objects = models.Manager()
    tenant_objects = TenantManager()

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_billing_ledger"
        verbose_name = "Billing Ledger Entry"
        verbose_name_plural = "Billing Ledger Entries"

    def __str__(self) -> str:
        return (
            f"₹{self.computed_charge} | {self.processing_cycle_stamp} → "
            f"{self.bank.tenant_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 7. FraudEvent
# ═══════════════════════════════════════════════════════════════════════════
class FraudEvent(UUIDBaseModel):
    """
    Velocity Lock Fraud Event.

    Records malicious devices that attempt to hit the API too many times
    across different tenants.
    """
    device_hash_mask = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The hashed device identifier that was burned.",
    )
    status = models.CharField(
        max_length=50,
        default="BURNED",
        help_text="Status of this device hash (e.g. BURNED).",
    )
    reason = models.TextField(
        help_text="Reason for burning (e.g. Velocity lock).",
    )

    class Meta(UUIDBaseModel.Meta):
        db_table = "finedge_fraud_event"
        verbose_name = "Fraud Event"
        verbose_name_plural = "Fraud Events"

    def __str__(self) -> str:
        return f"{self.status}: {self.device_hash_mask} ({self.reason})"


# ═══════════════════════════════════════════════════════════════════════════
# Contact Form (Public Support Inbox)
# ═══════════════════════════════════════════════════════════════════════════

class ContactMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "finedge_contact_message"
        app_label = "api_gateway"
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.first_name} {self.last_name} ({self.email})"