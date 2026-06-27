"""
FinEdge — API Gateway Views
=============================
Production API endpoints for the FinEdge Edge-ML Credit Scoring Platform.

Endpoints
---------
- ``POST /api/v1/score/``  — Submit edge metadata for TrustScore computation.
- ``GET  /api/health/``    — Health-check (public, no auth).

Security Layers
---------------
1. **API Key Authentication** — Every request must carry a valid
   ``Authorization: Api-Key <key>`` header.  The key is HMAC-SHA256
   hashed and matched against ``ApiCredential.hashed_key``.

2. **HMAC Signature Verification** — The Edge SDK signs the raw JSON
   body with the shared secret and attaches the hex digest in the
   ``X-FinEdge-Signature`` header.  The backend recomputes the HMAC
   and rejects tampered payloads with ``403 Forbidden``.

3. **Tenant Isolation** — The authenticated API key resolves to a
   ``Bank`` (tenant).  All database writes are scoped to that tenant
   via the ``TenantManager``.

4. **Atomic Transactions** — ``TrustScoreResult`` and ``BillingLedger``
   writes are wrapped in ``transaction.atomic()`` so a billing failure
   never orphans a score (and vice versa).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Final

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ApiCredential,
    Bank,
    BillingLedger,
    LoanApplication,
    LoanApplicationStep,
    SdkSession,
    TrustScoreResult,
    FEATURE_COLUMNS,
)
from .pipeline import (
    DECISION_FALLBACK_AA,
    WaterfallResult,
    evaluate_application,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("finedge.views")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# HMAC secret for payload signature verification
# In production, load from environment: os.getenv("FINEDGE_HMAC_SECRET")
HMAC_SECRET: Final[bytes] = getattr(
    settings,
    "FINEDGE_HMAC_SECRET",
    b"finedge_hmac_shared_secret_2026",
)
if isinstance(HMAC_SECRET, str):
    HMAC_SECRET_BYTES: Final[bytes] = HMAC_SECRET.encode("utf-8")
else:
    HMAC_SECRET_BYTES: Final[bytes] = HMAC_SECRET

# Per-API-call billing charge (INR)
PER_CALL_CHARGE: Final[Decimal] = Decimal("10.0000")

# API Key header name
API_KEY_HEADER: Final[str] = "HTTP_AUTHORIZATION"
API_KEY_PREFIX: Final[str] = "Api-Key "

# HMAC signature header
SIGNATURE_HEADER: Final[str] = "HTTP_X_FINEDGE_SIGNATURE"


# ═══════════════════════════════════════════════════════════════════════════
# Authentication helpers
# ═══════════════════════════════════════════════════════════════════════════
def _hash_api_key(raw_key: str) -> str:
    """
    Compute the HMAC-SHA256 hash of a raw API key.

    This matches the hash stored in ``ApiCredential.hashed_key``
    during key provisioning.
    """
    return hmac.new(
        HMAC_SECRET_BYTES,
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _authenticate_api_key(request: Request) -> ApiCredential | None:
    """
    Extract and validate the API key from the Authorization header.

    Returns the matching ``ApiCredential`` or ``None`` if invalid.
    """
    auth_header = request.META.get(API_KEY_HEADER, "")
    if not auth_header.startswith(API_KEY_PREFIX):
        return None

    raw_key = auth_header[len(API_KEY_PREFIX):].strip()
    if not raw_key:
        return None

    hashed = _hash_api_key(raw_key)

    try:
        credential = ApiCredential.objects.select_related("bank").get(
            hashed_key=hashed,
            is_active=True,
            bank__is_active=True,
        )
    except ApiCredential.DoesNotExist:
        return None

    # Update last-used timestamp (fire-and-forget, non-blocking)
    ApiCredential.objects.filter(pk=credential.pk).update(
        last_used_at=timezone.now(),
    )

    return credential


# ═══════════════════════════════════════════════════════════════════════════
# HMAC signature verification
# ═══════════════════════════════════════════════════════════════════════════
def _verify_hmac_signature(request: Request) -> bool:
    """
    Verify the HMAC-SHA256 signature in the ``X-FinEdge-Signature`` header
    against the raw request body.

    The Edge SDK computes::

        signature = HMAC-SHA256(shared_secret, raw_json_body).hexdigest()

    and attaches it as ``X-FinEdge-Signature: <hex_digest>``.
    """
    client_signature = request.META.get(SIGNATURE_HEADER, "")
    if not client_signature:
        logger.warning("HMAC verification failed: missing X-FinEdge-Signature header")
        return False

    # Use the raw body bytes (before DRF parsing) for HMAC computation
    raw_body = request.body
    expected_signature = hmac.new(
        HMAC_SECRET_BYTES,
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_signature, client_signature)
    if not is_valid:
        logger.warning(
            "HMAC verification failed: signature mismatch "
            "(expected=%s..., received=%s...)",
            expected_signature[:16], client_signature[:16],
        )
    return is_valid


# ═══════════════════════════════════════════════════════════════════════════
# Health check (public, no auth)
# ═══════════════════════════════════════════════════════════════════════════
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    """Simple health-check endpoint to verify the API is running."""
    return Response(
        {
            "status": "ok",
            "service": "finedge-api-gateway",
            "timestamp": timezone.now().isoformat(),
        },
        status=status.HTTP_200_OK,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Public Landing Page
# ═══════════════════════════════════════════════════════════════════════════
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny

def landing_page(request):
    return redirect('https://fin-edge-ten.vercel.app/devweb/index.html')

def api_docs(request: HttpRequest) -> HttpResponse:
    """Render the Developer API documentation portal."""
    return render(request, "api_gateway/api_docs.html")

def privacy_policy(request: HttpRequest) -> HttpResponse:
    """Render the privacy policy page."""
    return render(request, "api_gateway/privacy.html")

@api_view(["POST"])
@permission_classes([AllowAny])
def submit_contact_form(request: Request) -> Response:
    """Handle public contact form submission."""
    from .models import ContactMessage
    
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    email = request.data.get("email")
    message = request.data.get("message")
    
    if not all([first_name, last_name, email, message]):
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        
    ContactMessage.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        message=message
    )
    return Response({"status": "success", "message": "Message received."}, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════════════════
# Core scoring endpoint
# ═══════════════════════════════════════════════════════════════════════════
class SubmitEdgeMetadataView(APIView):
    """
    ``POST /api/v1/score/``

    Receive a mathematical feature vector from the Edge SDK, authenticate
    the partner bank, verify the HMAC signature, execute the underwriting
    waterfall, and persist results atomically.

    Request Headers
    ---------------
    - ``Authorization: Api-Key <key>``      — Partner bank API key.
    - ``X-FinEdge-Signature: <hex_digest>`` — HMAC-SHA256 of the raw body.

    Request Body (JSON)
    -------------------
    .. code-block:: json

        {
            "device_hash_mask": "a1b2c3d4...",
            "tracking_reference": "PARTNER-LOAN-12345",
            "mathematical_vector": {
                "device_age_days": 365,
                "utility_sms_count": 20,
                "battery_deaths_weekly": 1,
                "saved_contacts_ratio": 0.45,
                "financial_apps_count": 4,
                "average_monthly_balance": 25000.0,
                "lifetime_emi_bounces": 0
            }
        }

    Response (201 Created)
    ----------------------
    .. code-block:: json

        {
            "application_id": "uuid",
            "tracking_reference": "PARTNER-LOAN-12345",
            "decision": "ML_TRUSTSCORE_COMPUTED",
            "trust_score": 742,
            "default_probability": 0.2634,
            "is_thin_file": false,
            "model_version": "v1.0.0",
            "waterfall_step": 3
        }
    """

    # Disable DRF's default authentication/permission classes —
    # we handle auth manually via API key + HMAC.
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request) -> Response:
        """Process an Edge SDK metadata submission."""

        # ── 1. API Key Authentication ─────────────────────────────────────
        credential = _authenticate_api_key(request)
        if credential is None:
            logger.warning("Authentication failed: invalid or missing API key")
            return Response(
                {
                    "error": "Authentication failed",
                    "detail": "Invalid or missing API key.  "
                              "Provide a valid 'Authorization: Api-Key <key>' header.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        bank: Bank = credential.bank
        logger.info("Authenticated tenant: %s (%s)", bank.name, bank.tenant_code)

        # ── 2. HMAC Signature Verification ────────────────────────────────
        if not _verify_hmac_signature(request):
            return Response(
                {
                    "error": "Signature verification failed",
                    "detail": "HMAC-SHA256 signature in X-FinEdge-Signature header "
                              "does not match the request body.  "
                              "Payload may have been tampered with.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── 3. Extract & Validate Request Body ───────────────────────────
        data: dict[str, Any] = request.data

        device_hash_mask = data.get("device_hash_mask")
        tracking_reference = data.get("tracking_reference")
        mathematical_vector = data.get("mathematical_vector")

        # Field presence validation
        errors: dict[str, str] = {}
        if not device_hash_mask:
            errors["device_hash_mask"] = "This field is required."
        if not tracking_reference:
            errors["tracking_reference"] = "This field is required."
        if not mathematical_vector or not isinstance(mathematical_vector, dict):
            errors["mathematical_vector"] = (
                "This field is required and must be a JSON object "
                f"with keys: {FEATURE_COLUMNS}"
            )
        if errors:
            return Response(
                {"error": "Validation failed", "fields": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 5. Get Requested Amount ──────────────────────────────────────────
        requested_amount = data.get("requested_amount", 2000.00)

        # ── 6. Atomic Database Writes (Save Vector, Defer Score) ─────────────
        try:
            with transaction.atomic():
                # 6a. Create SDK session
                sdk_session = SdkSession.objects.create(
                    bank=bank,
                    device_hash_mask=device_hash_mask,
                )

                # 6b. Create loan application
                loan_app = LoanApplication.objects.create(
                    bank=bank,
                    sdk_session=sdk_session,
                    tracking_reference=tracking_reference,
                    current_step=LoanApplicationStep.SDK_RECEIVED,
                    requested_amount=requested_amount,
                    cibil_score=-1, # Automatically -1 for New to Credit
                )

                # 6c. Create empty TrustScoreResult to store the vector
                trust_score_record = TrustScoreResult.objects.create(
                    loan_application=loan_app,
                    mathematical_vector=mathematical_vector,
                    calculated_score=None,
                    default_probability=None,
                    model_version="v1.0.0",
                    is_thin_file=False,
                )

                logger.info(
                    "Received Edge SDK payload: app=%s amount=₹%s (Score deferred)",
                    loan_app.id, requested_amount,
                )

        except Exception as exc:
            logger.exception("Database write failed: %s", exc)
            return Response(
                {
                    "error": "Internal server error",
                    "detail": "Failed to persist application. Please retry.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── 7. Success Response ───────────────────────────────────────────
        return Response(
            {
                "application_id": str(loan_app.id),
                "tracking_reference": tracking_reference,
                "decision": "PENDING_OFFICER_REVIEW",
                "message": "Application submitted successfully.",
            },
            status=status.HTTP_201_CREATED,
        )

@api_view(["GET"])
@permission_classes([AllowAny])
def application_status_check(request: Request, application_id: str) -> Response:
    """Mobile app polling endpoint to get real-time status."""
    from django.shortcuts import get_object_or_404
    app = get_object_or_404(LoanApplication, id=application_id)
    
    trust = getattr(app, "trust_score", None)
    score = None
    if trust and trust.calculated_score is not None:
        score = trust.calculated_score
    
    return Response({
        "status": app.current_step,
        "trust_score": score,
    })

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def trigger_trust_score(request: Request, application_id: str) -> Response:
    """Officer-triggered TrustScore calculation (The ₹10 API Hit)."""
    from django.shortcuts import get_object_or_404
    from .pipeline import evaluate_application
    
    app = get_object_or_404(LoanApplication, id=application_id)
    
    if app.trust_score.calculated_score is not None:
        return Response({"error": "Score already computed."}, status=status.HTTP_400_BAD_REQUEST)
        
    vector = app.trust_score.mathematical_vector
    
    try:
        result = evaluate_application(vector)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    with transaction.atomic():
        app.trust_score.calculated_score = result.trust_score
        app.trust_score.default_probability = result.default_probability
        app.trust_score.is_thin_file = result.is_thin_file
        app.trust_score.save()
        
        if result.decision == DECISION_FALLBACK_AA:
            app.current_step = LoanApplicationStep.FALLBACK_REVIEW
        else:
            app.current_step = LoanApplicationStep.SCORE_COMPUTED
        app.save()
        
        BillingLedger.objects.create(
            bank=app.bank,
            computed_charge=PER_CALL_CHARGE,
            processing_cycle_stamp=datetime.now().strftime("%Y-%m"),
            description=f"Manual Officer TrustScore trigger — ref:{app.tracking_reference} score:{result.trust_score}"
        )
        
    return Response({"status": "success", "trust_score": result.trust_score})