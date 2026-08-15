import logging

from app.logging_config import PrivacyPreservingFormatter


def test_privacy_formatter_redacts_base64_and_vectors():
    formatter = PrivacyPreservingFormatter(fmt='%(message)s')
    
    # 1. Base64 payload redaction
    record1 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=1,
        msg="Processing image payload data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        args=(), exc_info=None
    )
    formatted1 = formatter.format(record1)
    assert "[REDACTED_BASE64_IMAGE]" in formatted1
    assert "iVBORw0KGgoAAAANSUh" not in formatted1

    # 2. Vector array redaction
    sample_vector = [0.1234, -0.5678, 0.9012, 0.3456, -0.7890, 0.1111]
    record2 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=1,
        msg=f"Generated embedding vector: {sample_vector}",
        args=(), exc_info=None
    )
    formatted2 = formatter.format(record2)
    assert "[REDACTED_EMBEDDING_VECTOR]" in formatted2
    assert "0.1234" not in formatted2
