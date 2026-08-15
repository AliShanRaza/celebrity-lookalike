import pytest
from app.services.calibration import MonotonicPlaceholderCalibrator, SigmoidCalibrator
from scripts.evaluate_calibration import evaluate_benchmark_distributions, generate_benchmark_pair


def test_sigmoid_calibrator_properties_and_monotonicity():
    calibrator = SigmoidCalibrator()

    assert calibrator.is_calibrated is True
    assert "sigmoid_calibrated" in calibrator.calibrator_type

    # Test monotonicity: increasing similarity yields strictly increasing score
    similarities = [-0.5, -0.1, 0.1, 0.25, 0.5, 0.8, 0.95]
    scores = [calibrator.calibrate(s) for s in similarities]

    assert scores == sorted(scores)
    assert all(0.0 <= s <= 100.0 for s in scores)


def test_fitted_calibrator_rating_category_separation():
    """
    Feeds representative raw similarity values for rating categories (strong, moderate, weak)
    through the fitted calibrator and asserts strict score band ordering:
    strong_match (> 80%) > moderate_match (50-80%) > weak_match (< 50%).
    """
    calibrator = SigmoidCalibrator(s_mid=0.22, steepness=12.0)

    # Typical ArcFace raw cosine similarity values per category
    strong_sim = 0.45   # strong_match
    moderate_sim = 0.25 # moderate_match
    weak_sim = -0.05    # weak_match

    score_strong = calibrator.calibrate(strong_sim)
    score_moderate = calibrator.calibrate(moderate_sim)
    score_weak = calibrator.calibrate(weak_sim)

    print(f"Strong match score: {score_strong}%")
    print(f"Moderate match score: {score_moderate}%")
    print(f"Weak match score: {score_weak}%")

    # Assert strict non-overlapping ordering
    assert score_strong > score_moderate > score_weak
    assert score_strong >= 80.0
    assert 50.0 <= score_moderate < 80.0
    assert score_weak < 50.0


def test_held_out_benchmark_distribution_evaluation():
    report = evaluate_benchmark_distributions(num_pairs=100)

    assert report["benchmark_sample_size"] == 200
    assert report["l2_norm_verification"] == "PASSED (all vectors unit norm 1.0)"

    linear_gap = report["before_linear_placeholder"]["separation_gap"]
    sigmoid_gap = report["after_sigmoid_calibrated"]["separation_gap"]

    # Sigmoid calibration must significantly expand the separation gap between positives and non-matches
    assert sigmoid_gap > linear_gap + 30.0
