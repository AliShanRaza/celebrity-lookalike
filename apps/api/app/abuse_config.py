from typing import List, Set
from pydantic import BaseModel, Field


class AbuseConfig(BaseModel):
    """
    Abuse mitigation and rate limiting policy configuration.
    """
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=10,
        description="Maximum match requests allowed per client per minute"
    )
    MAX_CONCURRENT_JOBS_PER_CLIENT: int = Field(
        default=2,
        description="Maximum active queued or processing jobs allowed per client"
    )
    BLOCKED_CLIENT_HASHES: Set[str] = Field(
        default_factory=set,
        description="Set of explicitly blocked hashed client identifiers"
    )
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum allowed upload payload size (10 MB)"
    )


abuse_config = AbuseConfig()
