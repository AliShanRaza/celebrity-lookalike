import hashlib
import hmac
from typing import Optional
from app.config import settings


def hash_client_identifier(ip_address: Optional[str], session_token: Optional[str] = None) -> str:
    """
    Hashes client IP address and optional session token using HMAC-SHA256 with the app's secret key.
    Guarantees that raw client IP addresses are NEVER stored in Redis rate limit buckets, job keys, or logs.
    """
    raw_identifier = f"ip:{ip_address or '0.0.0.0'}|session:{session_token or 'none'}"
    secret_bytes = settings.SECRET_KEY.encode("utf-8")
    
    hashed = hmac.new(secret_bytes, raw_identifier.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"client_hash:{hashed[:32]}"
