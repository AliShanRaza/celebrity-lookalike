import io
import ipaddress
import logging
import socket
from urllib.parse import urlparse
from typing import Tuple
import httpx
from PIL import Image

from app.config import settings
from app.services.image_intake import (
    SecureImageIntakeService,
    MAX_COMPRESSED_SIZE_BYTES,
    ALLOWED_MIME_TYPES,
)
from app.services.recognition.base import InvalidImageError

logger = logging.getLogger(__name__)

# Security Constants
MAX_REDIRECT_CAP = 3
FETCH_TIMEOUT_SECONDS = 5.0
SAFE_USER_AGENT = "CelebrityLookalikeIntake/1.0"


class SSRFProtectionError(InvalidImageError):
    """Raised when URL validation fails SSRF security checks."""
    def __init__(self, message: str = "Forbidden URL host or internal IP target."):
        super().__init__(message)


class SecureURLIntakeService:
    """
    SSRF-protected URL image intake service.
    Enforces feature flag check, strict http/https scheme, DNS resolution IP filtering
    (blocking loopback, private, link-local, multicast, and cloud metadata IPs),
    redirect cap, timeout, content-length limit, streaming size limit, and MIME validation.
    """

    @staticmethod
    def validate_target_ip(ip_str: str) -> None:
        """
        Validates IP address against loopback, private, link-local, multicast, and reserved ranges.
        """
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFProtectionError(f"Invalid IP address format '{ip_str}'.")

        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            logger.warning(f"SSRF Check Rejected: IP address {ip_str} falls within a restricted internal/private range.")
            raise SSRFProtectionError("Access to private, loopback, or internal IP addresses is prohibited.")

    @staticmethod
    def validate_url(url_str: str) -> Tuple[str, str, int]:
        """
        Parses and validates target URL scheme and resolves DNS hostnames to ensure no internal targets.
        Returns tuple of (scheme, hostname, port).
        """
        if not url_str or not url_str.strip():
            raise InvalidImageError("Empty URL string provided.")

        parsed = urlparse(url_str.strip())

        # 1. Strict Protocol Check (http/https only)
        scheme = (parsed.scheme or "").lower()
        if scheme not in ("http", "https"):
            raise InvalidImageError(f"Forbidden URL scheme '{scheme}'. Only http and https protocols are allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise InvalidImageError("Invalid URL: Missing hostname.")

        hostname_lower = hostname.lower()

        # 2. Block explicit dangerous hostnames / cloud metadata endpoints
        blocked_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254.169.254", "metadata.google.internal"}
        if hostname_lower in blocked_hosts:
            raise SSRFProtectionError(f"Forbidden host '{hostname}'. Localhost and internal metadata endpoints are blocked.")

        port = parsed.port or (443 if scheme == "https" else 80)

        # 3. DNS Resolution IP Check
        try:
            addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not addr_info:
                raise SSRFProtectionError(f"Could not resolve hostname '{hostname}'.")

            for family, socktype, proto, canonname, sockaddr in addr_info:
                ip_addr = sockaddr[0]
                SecureURLIntakeService.validate_target_ip(ip_addr)

        except socket.gaierror as e:
            logger.warning(f"DNS Resolution failed for hostname '{hostname}': {str(e)}")
            raise InvalidImageError(f"Failed to resolve target hostname '{hostname}'.")

        return scheme, hostname, port

    @staticmethod
    def fetch_image_from_url(url_str: str) -> Tuple[bytes, Image.Image]:
        """
        Fetches an image from an external URL with full SSRF protection.
        Enforces feature flag, URL/IP validation, timeout, redirect limits, content-length limit,
        streaming size limit, and MIME checks.
        """
        # Feature Flag Check
        if not settings.ENABLE_URL_UPLOADS:
            raise InvalidImageError("URL image uploads are disabled by feature flag configuration.")

        # Validate URL scheme & resolved target IP
        SecureURLIntakeService.validate_url(url_str)

        # Prepare safe HTTP client options (no internal credentials, custom User-Agent)
        headers = {
            "User-Agent": SAFE_USER_AGENT,
            "Accept": "image/jpeg, image/png, image/webp, image/*",
        }

        try:
            client = httpx.Client(
                follow_redirects=True,
                max_redirects=MAX_REDIRECT_CAP,
                timeout=FETCH_TIMEOUT_SECONDS,
                headers=headers
            )

            with client.stream("GET", url_str) as response:
                # Validate HTTP status code
                if response.status_code != 200:
                    raise InvalidImageError(f"Remote server returned HTTP status {response.status_code}.")

                # Validate Content-Type header
                content_type = response.headers.get("Content-Type", "").lower().split(";")[0].strip()
                if content_type and content_type not in ALLOWED_MIME_TYPES and not content_type.startswith("image/"):
                    raise InvalidImageError(f"Remote server returned unsupported Content-Type '{content_type}'.")

                # Validate Content-Length header if present
                content_length_hdr = response.headers.get("Content-Length")
                if content_length_hdr and content_length_hdr.isdigit():
                    content_length = int(content_length_hdr)
                    if content_length > MAX_COMPRESSED_SIZE_BYTES:
                        raise InvalidImageError(f"URL image Content-Length ({content_length} bytes) exceeds limit of 10MB.")

                # Stream response body while enforcing cumulative size limit
                downloaded = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    downloaded.extend(chunk)
                    if len(downloaded) > MAX_COMPRESSED_SIZE_BYTES:
                        raise InvalidImageError("Remote image payload exceeds maximum allowed limit of 10MB.")

                image_bytes = bytes(downloaded)

        except httpx.TimeoutException:
            logger.warning(f"URL fetch timed out after {FETCH_TIMEOUT_SECONDS}s.")
            raise InvalidImageError(f"Request to URL timed out after {FETCH_TIMEOUT_SECONDS} seconds.")
        except httpx.TooManyRedirects:
            logger.warning(f"URL fetch exceeded maximum redirect limit of {MAX_REDIRECT_CAP}.")
            raise InvalidImageError(f"URL fetch exceeded maximum redirect limit of {MAX_REDIRECT_CAP}.")
        except httpx.HTTPError as e:
            if isinstance(e, (InvalidImageError, SSRFProtectionError)):
                raise
            logger.warning(f"HTTP error fetching URL: {str(e)}")
            raise InvalidImageError(f"Failed to fetch image from URL: {str(e)}")

        # Process downloaded bytes via SecureImageIntakeService (format, pixels, EXIF, RGB)
        return SecureImageIntakeService.process_image_bytes(image_bytes, filename_hint=url_str)
