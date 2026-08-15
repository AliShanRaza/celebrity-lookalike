import io
import json
import math
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class ScoreCalibrator(ABC):
    """
    Abstract interface for calibrating raw cosine similarity scores [-1.0, 1.0]
    into user-facing entertainment resemblance scores [0.0, 100.0].
    """

    @abstractmethod
    def calibrate(self, raw_similarity: float) -> float:
        """
        Maps raw cosine similarity to calibrated resemblance score [0.0, 100.0].
        """
        pass

    @property
    @abstractmethod
    def calibrator_type(self) -> str:
        """Returns the type identifier of this calibrator."""
        pass

    @property
    @abstractmethod
    def is_calibrated(self) -> bool:
        """Returns True if trained on identity pair datasets, False if uncalibrated placeholder."""
        pass


class MonotonicPlaceholderCalibrator(ScoreCalibrator):
    """
    Documented monotonic placeholder score calibrator.
    Maps raw cosine similarity s in [-1.0, 1.0] monotonically into [0.0, 100.0].
    
    Formula:
    resemblance = max(0.0, min(100.0, ((s + 1.0) / 2.0) * 100.0))
    
    Explicitly labeled as UNCALIBRATED.
    """

    def calibrate(self, raw_similarity: float) -> float:
        s = max(-1.0, min(1.0, float(raw_similarity)))
        resemblance = ((s + 1.0) / 2.0) * 100.0
        return round(max(0.0, min(100.0, resemblance)), 2)

    @property
    def calibrator_type(self) -> str:
        return "uncalibrated_monotonic_placeholder_v1"

    @property
    def is_calibrated(self) -> bool:
        return False


class SigmoidCalibrator(ScoreCalibrator):
    """
    Calibrated Resemblance Score Provider using a logistic sigmoid curve.
    Dynamically loads fitted s_mid and steepness parameters from serialized weights file
    (e.g., calibration_weights.json) if available, falling back to tuned defaults.
    """

    def __init__(
        self,
        s_mid: Optional[float] = None,
        steepness: Optional[float] = None,
        weights_path: Optional[str] = None
    ):
        self._weights_path = weights_path or os.path.join(
            os.path.dirname(__file__), "calibration_weights.json"
        )
        self._s_mid = 0.25 if s_mid is None else s_mid
        self._steepness = 8.0 if steepness is None else steepness
        self._calibrator_type = "sigmoid_calibrated_v1"

        if os.path.exists(self._weights_path):
            try:
                with open(self._weights_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._s_mid = float(data.get("s_mid", self._s_mid))
                    self._steepness = float(data.get("steepness", self._steepness))
                    self._calibrator_type = data.get("calibrator_type", self._calibrator_type)
                    logger.info(f"Loaded fitted calibration parameters: s_mid={self._s_mid}, steepness={self._steepness}")
            except Exception as exc:
                logger.warning(f"Could not load calibration weights from '{self._weights_path}': {exc}")

    def calibrate(self, raw_similarity: float) -> float:
        s = max(-1.0, min(1.0, float(raw_similarity)))
        exponent = -self._steepness * (s - self._s_mid)
        # Avoid overflow for extreme exponents
        exponent = max(-50.0, min(50.0, exponent))
        sig = 1.0 / (1.0 + math.exp(exponent))
        score = sig * 100.0
        return round(max(0.0, min(100.0, score)), 1)

    @property
    def calibrator_type(self) -> str:
        return self._calibrator_type

    @property
    def is_calibrated(self) -> bool:
        return True
