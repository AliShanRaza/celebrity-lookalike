import pytest
from scripts.trace_pipeline import create_known_test_image_bytes, trace_test_image_pipeline


def test_end_to_end_pipeline_trace_regression():
    """
    Regression test verifying end-to-end trace parameters:
    1. Intake & decoded resolution
    2. Detector bounding box & 5 facial landmarks
    3. Aligned crop dimensions (112x112) & preprocessing tensor shape [1, 3, 112, 112]
    4. 512d vector embedding with strict L2 norm approx 1.0
    5. Top 20 candidate ranking order
    6. Distinct identity aggregation
    7. Monotonic score calibrator output
    """
    test_bytes = create_known_test_image_bytes(width=224, height=224)
    trace = trace_test_image_pipeline(test_bytes)

    # 1. Intake verification
    assert trace["intake"]["decoded_resolution"] == "224x224"
    assert trace["intake"]["color_mode"] == "RGB"

    # 2. Detection & 5 landmarks verification
    assert trace["face_detection"]["bounding_box"] == (0, 0, 224, 224)
    landmarks = trace["face_detection"]["landmarks"]
    assert set(landmarks.keys()) == {"left_eye", "right_eye", "nose", "mouth_left", "mouth_right"}

    # 3. Alignment & Preprocessing verification
    assert trace["alignment"]["crop_dimensions"] == "112x112"
    prep = trace["alignment"]["preprocessing"]
    assert prep["channel_order"] == "RGB"
    assert prep["tensor_shape"] == [1, 3, 112, 112]
    assert prep["scaling_formula"] == "(x - 127.5) / 128.0"

    # 4. Embedding & L2 Unit Norm verification
    emb = trace["embedding"]
    assert emb["dimension"] == 512
    assert emb["all_finite"] is True
    assert abs(emb["l2_norm"] - 1.0) < 1e-4

    # 5. Top 20 Hits verification
    hits = trace["top_20_hits"]
    assert len(hits) == 20
    # Verify ranking order: cosine distances must be strictly ascending
    distances = [h["cosine_distance"] for h in hits]
    assert distances == sorted(distances)

    # 6. Identity Aggregation verification
    agg = trace["identity_aggregation"]
    assert agg["distinct_celebrities_count"] == 20
    assert agg["best_hit_name"] == "Celebrity Identity #1"

    # 7. Score Mapping verification
    score_map = trace["score_mapping"]
    assert score_map["is_calibrated"] is False
    assert score_map["calibrator_type"] == "uncalibrated_monotonic_placeholder_v1"
