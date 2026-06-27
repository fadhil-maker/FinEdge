from django.contrib import admin
from .models import TrustScoreResult, LoanApplication, Bank, ApiCredential

@admin.register(TrustScoreResult)
class TrustScoreResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan_application', 'calculated_score', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('tracking_reference', 'bank', 'current_step', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant_code', 'is_active')

@admin.register(ApiCredential)
class ApiCredentialAdmin(admin.ModelAdmin):
    list_display = ('label', 'bank', 'is_active')
