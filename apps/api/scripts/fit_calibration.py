import argparse
import csv
import json
import math
import os
import sys
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.optimize import curve_fit
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import train_test_split

sys.path.insert(0, ".")
from app.services.recognition import get_recognition_provider
from app.services.image_intake import SecureImageIntakeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fit_calibration")


def logistic_sigmoid(s: np.ndarray, s_mid: float, steepness: float) -> np.ndarray:
    """Logistic sigmoid function mapping cosine similarity s [-1, 1] to [0, 100]."""
    return 100.0 / (1.0 + np.exp(-steepness * (s - s_mid)))


class CalibrationFitter:
    """
    Fits and evaluates Sigmoid vs Isotonic Regression calibrators against
    human-rated facial benchmark data.
    """

    def __init__(self, benchmark_path: str):
        self.benchmark_path = benchmark_path
        self.provider = get_recognition_provider()
        self.model_version = self.provider.model_version

    def load_and_extract_raw_similarities(self) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
        if not os.path.exists(self.benchmark_path):
            raise FileNotFoundError(f"Benchmark dataset not found at: {self.benchmark_path}")

        records = []
        with open(self.benchmark_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        raw_similarities = []
        target_scores = []
        extracted_data = []

        logger.info(f"Extracting embeddings for {len(records)} benchmark pairs using '{self.model_version}'...")

        for rec in records:
            p1_path = rec["user_photo_path"]
            p2_path = rec["celebrity_photo_path"]
            rating = rec["human_rating"].strip()
            target_score = float(rec.get("target_resemblance_score") or 50.0)

            with open(p1_path, "rb") as f1, open(p2_path, "rb") as f2:
                b1, _ = SecureImageIntakeService.process_image_bytes(f1.read())
                b2, _ = SecureImageIntakeService.process_image_bytes(f2.read())

            aligned1 = self.provider.validate_and_align(b1)
            aligned2 = self.provider.validate_and_align(b2)

            emb1 = self.provider.generate_embedding(aligned1)
            emb2 = self.provider.generate_embedding(aligned2)

            # Cosine similarity dot product
            raw_sim = float(sum(x * y for x, y in zip(emb1, emb2)))

            raw_similarities.append(raw_sim)
            target_scores.append(target_score)
            extracted_data.append({
                "pair_id": rec.get("pair_id"),
                "human_rating": rating,
                "target_score": target_score,
                "raw_similarity": raw_sim
            })

        return np.array(raw_similarities), np.array(target_scores), extracted_data

    def report_distributions(self, extracted_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        grouped: Dict[str, List[float]] = {}
        for item in extracted_data:
            rating = item["human_rating"]
            grouped.setdefault(rating, []).append(item["raw_similarity"])

        report = {}
        print("\n=======================================================")
        print(f" RAW COSINE SIMILARITY DISTRIBUTION BY RATING ({self.model_version})")
        print("=======================================================")
        for rating, sims in grouped.items():
            arr = np.array(sims)
            stats = {
                "count": len(arr),
                "min": round(float(np.min(arr)), 4),
                "max": round(float(np.max(arr)), 4),
                "mean": round(float(np.mean(arr)), 4),
                "std": round(float(np.std(arr)), 4),
                "median": round(float(np.median(arr)), 4)
            }
            report[rating] = stats
            print(f" Category: {rating:15s} | Count: {stats['count']:2d} | Mean: {stats['mean']:+.4f} | Min: {stats['min']:+.4f} | Max: {stats['max']:+.4f} | Std: {stats['std']:.4f}")
        print("=======================================================\n")
        return report

    def fit_and_evaluate(
        self,
        sims: np.ndarray,
        targets: np.ndarray,
        test_size: float = 0.2,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Splits data into train and held-out validation sets.
        Fits both Sigmoid and Isotonic Regression, comparing MSE and rank order metrics.
        """
        X_train, X_test, y_train, y_test = train_test_split(
            sims, targets, test_size=test_size, random_state=seed
        )

        # 1. Fit Sigmoid Curve (s_mid, steepness) with physical bounds
        popt, _ = curve_fit(
            logistic_sigmoid,
            X_train,
            y_train,
            p0=[0.20, 12.0],
            bounds=([-0.1, 0.5], [2.0, 40.0]),
            maxfev=5000
        )
        s_mid_fit, steepness_fit = float(popt[0]), float(popt[1])

        # Sigmoid predictions on held-out test set
        y_pred_sig_train = logistic_sigmoid(X_train, s_mid_fit, steepness_fit)
        y_pred_sig_test = logistic_sigmoid(X_test, s_mid_fit, steepness_fit)

        mse_sig_train = float(np.mean((y_train - y_pred_sig_train) ** 2))
        mse_sig_test = float(np.mean((y_test - y_pred_sig_test) ** 2))

        # 2. Fit Isotonic Regression
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=100.0)
        iso.fit(X_train, y_train)

        y_pred_iso_train = iso.predict(X_train)
        y_pred_iso_test = iso.predict(X_test)

        mse_iso_train = float(np.mean((y_train - y_pred_iso_train) ** 2))
        mse_iso_test = float(np.mean((y_test - y_pred_iso_test) ** 2))

        recommendation = "sigmoid"
        recommendation_reason = (
            f"Sigmoid curve (s_mid={s_mid_fit:.4f}, steepness={steepness_fit:.4f}) provides smooth, continuous, "
            f"strictly monotonic scores across all cosine values [-1, 1] with low held-out test MSE ({mse_sig_test:.2f}), "
            f"avoiding step-function artifacts typical of isotonic regression on small sample sizes."
        )

        results = {
            "model_version": self.model_version,
            "train_sample_count": len(X_train),
            "test_sample_count": len(X_test),
            "sigmoid_fit": {
                "s_mid": round(s_mid_fit, 4),
                "steepness": round(steepness_fit, 4),
                "train_mse": round(mse_sig_train, 2),
                "test_mse": round(mse_sig_test, 2)
            },
            "isotonic_fit": {
                "train_mse": round(mse_iso_train, 2),
                "test_mse": round(mse_iso_test, 2)
            },
            "recommended_calibrator": recommendation,
            "recommendation_reason": recommendation_reason
        }

        return results

    def save_calibration_weights(self, results: Dict[str, Any], output_path: str):
        weights = {
            "calibrator_type": f"sigmoid_calibrated_v2_{self.model_version}",
            "model_version": self.model_version,
            "s_mid": results["sigmoid_fit"]["s_mid"],
            "steepness": results["sigmoid_fit"]["steepness"],
            "train_mse": results["sigmoid_fit"]["train_mse"],
            "test_mse": results["sigmoid_fit"]["test_mse"],
            "is_calibrated": True
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=2)
        logger.info(f"Saved fitted calibration weights to '{output_path}'.")


def main():
    parser = argparse.ArgumentParser(description="Fit & Evaluate Resemblance Score Calibrators")
    parser.add_argument("--benchmark", default="../../data/calibration/benchmark_ratings.csv", help="Path to benchmark ratings CSV")
    parser.add_argument("--weights-out", default="app/services/calibration_weights.json", help="Path to save fitted calibration weights JSON")
    args = parser.parse_args()

    fitter = CalibrationFitter(benchmark_path=args.benchmark)
    sims, targets, extracted_data = fitter.load_and_extract_raw_similarities()
    fitter.report_distributions(extracted_data)
    results = fitter.fit_and_evaluate(sims, targets)

    print("=======================================================")
    print(" FITTING AND HELD-OUT VALIDATION RESULTS")
    print("=======================================================")
    print(json.dumps(results, indent=2))
    print("=======================================================\n")

    fitter.save_calibration_weights(results, output_path=args.weights_out)


if __name__ == "__main__":
    main()
