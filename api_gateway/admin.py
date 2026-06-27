from django.contrib import admin
from .models import TrustScore, PayloadLog

@admin.register(TrustScore)
class TrustScoreAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'score', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('device_id',)
    readonly_fields = ('created_at',)

@admin.register(PayloadLog)
class PayloadLogAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'ip_address', 'received_at')
    search_fields = ('device_id', 'ip_address')
    readonly_fields = ('received_at',)
