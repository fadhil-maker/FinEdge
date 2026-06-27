import logging
from datetime import timedelta
from django.utils import timezone
from .models import SdkSession, FraudEvent

logger = logging.getLogger("finedge.security")

def check_velocity_lock(device_hash: str) -> bool:
    """
    Check if a device is hitting too many tenants in the last 24 hours.

    If count >= 2 across different tenant_codes, mark as BURNED in FraudEvent
    and return True (locked). Otherwise False (allow).
    """
    cutoff = timezone.now() - timedelta(hours=24)

    # Check if already burned
    if FraudEvent.objects.filter(device_hash_mask=device_hash, status="BURNED").exists():
        return True

    # Count distinct tenants hit in the last 24 hours
    distinct_tenants = (
        SdkSession.objects.filter(
            device_hash_mask=device_hash,
            created_at__gte=cutoff
        )
        .values("bank__tenant_code")
        .distinct()
        .count()
    )

    if distinct_tenants >= 2:
        logger.warning(f"Velocity lock triggered for device {device_hash}. Tenants hit: {distinct_tenants}")
        FraudEvent.objects.create(
            device_hash_mask=device_hash,
            status="BURNED",
            reason=f"Velocity lock: Hit {distinct_tenants} tenants in 24 hours."
        )
        return True

    return False
