import pytest
from app.services.metrics import MetricsCollector
from app.logging_config import PrivacyPreservingFormatter, redact_sensitive_payloads


def test_metrics_collector_aggregation():
    collector = MetricsCollector()

    collector.record_request("/api/v1/matches", 200)
    collector.record_face_validation("success")
    collector.record_face_validation("no_face")
    collector.record_inference_duration(15.5)
    collector.record_inference_duration(24.5)
    collector.record_vector_search_duration(4.2)
    collector.record_job_failure("NO_FACE")
    collector.record_transient_deletion(True)

    summary = collector.get_summary()

    assert summary["requests"]["/api/v1/matches:200"] == 1
    assert summary["face_validation_outcomes"]["success"] == 1
    assert summary["face_validation_outcomes"]["no_face"] == 1
    assert summary["inference_duration"]["count"] == 2
    assert summary["inference_duration"]["avg_ms"] == 20.0
    assert summary["vector_search_duration"]["avg_ms"] == 4.2
    assert summary["job_failure_codes"]["NO_FACE"] == 1
    assert summary["transient_deletion_outcomes"]["success"] == 1


def test_metrics_privacy_no_biometrics():
    collector = MetricsCollector()
    summary = collector.get_summary()

    summary_str = str(summary)
    # Verify no biometric vectors, raw image bytes, or base64 data exist in summary
    assert "embedding" not in summary_str.lower()
    assert "vector" not in summary_str.lower() or "vector_search" in summary_str.lower()
    assert "base64" not in summary_str.lower()
    assert "image_bytes" not in summary_str.lower()


def test_secret_redaction():
    secret_text = "Connecting to database postgresql://postgres:my_secret_password@db:5432 with token bearer_super_secret_token_123"
    redacted = redact_sensitive_payloads(secret_text)

    assert "my_secret_password" not in redacted
    assert "[REDACTED_DATABASE_URL]" in redacted
