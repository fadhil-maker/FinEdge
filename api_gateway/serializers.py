"""
FinEdge — API Gateway Serializers (Phase 2 Stub)
=================================================
Placeholder serializers aligned with the new multi-tenant schema.
These will be fully implemented in Phase 3 (API Gateway & Waterfall Logic).
"""

from rest_framework import serializers

from .models import (
    Bank,
    LoanApplication,
    SdkSession,
    TrustScoreResult,
)


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ["id", "name", "tenant_code", "is_active"]
        read_only_fields = ["id"]


class SdkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SdkSession
        fields = ["id", "bank", "device_hash_mask", "created_at"]
        read_only_fields = ["id", "created_at"]


class TrustScoreResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustScoreResult
        fields = [
            "id",
            "loan_application",
            "mathematical_vector",
            "calculated_score",
            "default_probability",
            "model_version",
            "is_thin_file",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "calculated_score",
            "default_probability",
            "model_version",
            "is_thin_file",
            "created_at",
        ]


class LoanApplicationSerializer(serializers.ModelSerializer):
    trust_score = TrustScoreResultSerializer(read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "bank",
            "sdk_session",
            "tracking_reference",
            "current_step",
            "trust_score",
            "created_at",
        ]
        read_only_fields = ["id", "current_step", "created_at"]