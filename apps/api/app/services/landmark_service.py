from typing import Dict, List, Any

class LandmarkService:
    """
    Decoupled UI visualization helper service for facial landmark points.
    FMT/formats raw facial keypoints into tight, bounded facial contour coordinates
    suitable for frontend SVG overlay rendering without touching face recognition math.
    """

    @staticmethod
    def format_ui_landmarks(raw_landmarks: Dict[str, List[Dict[str, float]]]) -> Dict[str, List[Dict[str, float]]]:
        if not raw_landmarks:
            return LandmarkService.get_default_bounded_landmarks()

        eyebrows = raw_landmarks.get("eyebrows", [])
        left_eye = raw_landmarks.get("left_eye", [])
        right_eye = raw_landmarks.get("right_eye", [])
        nose = raw_landmarks.get("nose", [])
        mouth = raw_landmarks.get("mouth", [])

        # Compute facial landmark feature center and bounds for tight jawline contour
        all_feature_pts = eyebrows + left_eye + right_eye + nose + mouth
        if not all_feature_pts:
            return LandmarkService.get_default_bounded_landmarks()

        xs = [pt["x"] for pt in all_feature_pts]
        ys = [pt["y"] for pt in all_feature_pts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        center_x = (min_x + max_x) / 2.0
        width_span = max_x - min_x
        height_span = max_y - min_y

        # Bounded jawline contour around lower face (bounded strictly above neck/chest: y <= 0.68)
        left_jaw = {"x": round(max(0.05, center_x - width_span * 0.9), 4), "y": round(min_y + height_span * 0.3, 4)}
        chin_tip = {"x": round(center_x, 4), "y": round(min(0.68, max_y + height_span * 0.35), 4)}
        right_jaw = {"x": round(min(0.95, center_x + width_span * 0.9), 4), "y": round(min_y + height_span * 0.3, 4)}

        return {
            "eyebrows": eyebrows,
            "left_eye": left_eye,
            "right_eye": right_eye,
            "nose": nose,
            "mouth": mouth,
            "contour": [left_jaw, chin_tip, right_jaw]
        }

    @staticmethod
    def get_default_bounded_landmarks() -> Dict[str, List[Dict[str, float]]]:
        """Returns clean canonical facial landmark coordinates bounded to face region."""
        return {
            "eyebrows": [{"x": 0.35, "y": 0.30}, {"x": 0.65, "y": 0.30}],
            "left_eye": [{"x": 0.38, "y": 0.38}],
            "right_eye": [{"x": 0.62, "y": 0.38}],
            "nose": [{"x": 0.50, "y": 0.52}],
            "mouth": [{"x": 0.40, "y": 0.65}, {"x": 0.60, "y": 0.65}],
            "contour": [{"x": 0.25, "y": 0.42}, {"x": 0.50, "y": 0.68}, {"x": 0.75, "y": 0.42}]
        }
