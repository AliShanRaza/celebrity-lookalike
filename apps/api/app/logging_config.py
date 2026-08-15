import logging
import re
import sys
from typing import Any, Dict

DATABASE_URL_PATTERN = re.compile(r'postgres(?:ql)?\+?[a-zA-Z0-9_]*://[^:@\s]+:[^@\s]+@[^\s]+', re.IGNORECASE)
BEARER_TOKEN_PATTERN = re.compile(r'bearer\s+[A-Za-z0-9_\-\.]+', re.IGNORECASE)
BASE64_PATTERN = re.compile(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', re.IGNORECASE)
LONG_HEX_OR_B64 = re.compile(r'([A-Za-z0-9+/=]{100,})')
FLOAT_VECTOR_PATTERN = re.compile(r'\[(?:\s*-?\d+\.\d+\s*,?\s*){5,}\]')


def redact_sensitive_payloads(text: str) -> str:
    """Redacts secrets, database URLs, bearer tokens, base64 strings, and raw float vectors from string payloads."""
    if not text:
        return text
    text = DATABASE_URL_PATTERN.sub('[REDACTED_DATABASE_URL]', text)
    text = BEARER_TOKEN_PATTERN.sub('Bearer [REDACTED_TOKEN]', text)
    text = BASE64_PATTERN.sub('[REDACTED_BASE64_IMAGE]', text)
    text = LONG_HEX_OR_B64.sub('[REDACTED_LARGE_PAYLOAD]', text)
    text = FLOAT_VECTOR_PATTERN.sub('[REDACTED_EMBEDDING_VECTOR]', text)
    return text


class PrivacyPreservingFormatter(logging.Formatter):
    """
    Log formatter that prevents leaking raw image content, secrets,
    base64 strings, or numeric vector embeddings to standard output logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return redact_sensitive_payloads(formatted)


def setup_logging() -> None:
    """Configures privacy-compliant logger."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove pre-existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = PrivacyPreservingFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
