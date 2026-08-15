import io
import time
import math
import uuid
from typing import List, Dict, Any, Tuple
from PIL import Image

from app.services.image_intake import SecureImageIntakeService
from app.services.recognition.real import RealRecognitionProvider
from app.services.aggregation import QualityWeightedTopKAggregator
from app.services.calibration import SigmoidCalibrator
from app.schemas.matching import CelebrityMatchItem, MatchResultResponse
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding


def generate_profiling_image_bytes(width: int = 640, height: int = 640) -> bytes:
    """Generates a standard test portrait image for latency profiling."""
    img = Image.new("RGB", (width, height), color=(180, 140, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def profile_pipeline_stages(
    image_bytes: bytes,
    warmup_count: int = 5,
    benchmark_count: int = 20
) -> Dict[str, Any]:
    """
    Profiles 5 pipeline stages separately across warm requests:
    1. Image Decode & Preprocessing
    2. Face Detection & Alignment
    3. Embedding Inference & L2 Normalization
    4. Vector Search (pgvector cosine query simulation)
    5. Aggregation, Calibration & Serialization
    """
    provider = RealRecognitionProvider()
    aggregator = QualityWeightedTopKAggregator()
    calibrator = SigmoidCalibrator()

    # Pre-generate synthetic candidate vector search dataset (200 candidates)
    synthetic_candidates = []
    for idx in range(200):
        c_id = uuid.uuid4()
        c_name = f"Celebrity #{idx+1}"
        c_gender = "male" if idx % 2 == 0 else "female"
        dist = 0.05 + (idx * 0.002)
        emb_obj = CelebrityEmbedding(id=uuid.uuid4(), celebrity_id=c_id)
        img_obj = CelebrityImage(id=uuid.uuid4(), celebrity_id=c_id, image_url=f"https://img.example.com/{idx}.jpg")
        celeb_obj = Celebrity(id=c_id, name=c_name, gender=c_gender, bio=f"Bio {idx}")
        synthetic_candidates.append((emb_obj, img_obj, celeb_obj, dist))

    stage_timings: Dict[str, List[float]] = {
        "1_decode": [],
        "2_detection": [],
        "3_inference": [],
        "4_vector_search": [],
        "5_serialization": [],
        "total": []
    }

    total_runs = warmup_count + benchmark_count

    for run_idx in range(total_runs):
        is_warmup = (run_idx < warmup_count)

        t_start_total = time.perf_counter_ns()

        # Stage 1: Decode & Preprocessing
        t1_start = time.perf_counter_ns()
        processed_bytes, rgb_img = SecureImageIntakeService.process_image_bytes(image_bytes, filename_hint="profile.jpg")
        t1_elapsed = (time.perf_counter_ns() - t1_start) / 1e6

        # Stage 2: Detection & Alignment
        t2_start = time.perf_counter_ns()
        aligned_crop_bytes = provider.validate_and_align(processed_bytes)
        t2_elapsed = (time.perf_counter_ns() - t2_start) / 1e6

        # Stage 3: Embedding Inference & Normalization
        t3_start = time.perf_counter_ns()
        embedding = provider.generate_embedding(aligned_crop_bytes)
        t3_elapsed = (time.perf_counter_ns() - t3_start) / 1e6

        # Stage 4: Vector Nearest-Neighbor Search (pgvector query)
        t4_start = time.perf_counter_ns()
        candidates = []
        for emb_obj, img_obj, celeb_obj, base_dist in synthetic_candidates:
            dot_sim = sum(embedding[i] * 0.0442 for i in range(512))
            sim_dist = max(0.0, 1.0 - dot_sim)
            candidates.append((emb_obj, img_obj, celeb_obj, sim_dist))
        t4_elapsed = (time.perf_counter_ns() - t4_start) / 1e6

        # Stage 5: Aggregation, Calibration & Pydantic Serialization
        t5_start = time.perf_counter_ns()
        celeb_best_map = aggregator.aggregate_candidate_hits(candidates)

        distinct_matches = []
        for celeb_id, (aggregated_sim, image_url, celeb) in celeb_best_map.items():
            resemblance = calibrator.calibrate(aggregated_sim)
            match_item = CelebrityMatchItem(
                celebrity_id=celeb.id,
                name=celeb.name,
                gender=celeb.gender.lower(),
                image_url=image_url,
                resemblance_score=resemblance,
                bio=celeb.bio
            )
            distinct_matches.append(match_item)

        distinct_matches.sort(key=lambda item: item.resemblance_score, reverse=True)
        male_matches = [m for m in distinct_matches if m.gender == "male"][:10]
        female_matches = [m for m in distinct_matches if m.gender == "female"][:10]
        overall_matches = distinct_matches[:10]

        res = MatchResultResponse(
            request_id=str(uuid.uuid4()),
            model_version="profile_v1",
            score_version=calibrator.calibrator_type,
            male_matches=male_matches,
            female_matches=female_matches,
            overall_matches=overall_matches
        )
        json_output = res.model_dump_json()
        t5_elapsed = (time.perf_counter_ns() - t5_start) / 1e6

        t_total_elapsed = (time.perf_counter_ns() - t_start_total) / 1e6

        if not is_warmup:
            stage_timings["1_decode"].append(t1_elapsed)
            stage_timings["2_detection"].append(t2_elapsed)
            stage_timings["3_inference"].append(t3_elapsed)
            stage_timings["4_vector_search"].append(t4_elapsed)
            stage_timings["5_serialization"].append(t5_elapsed)
            stage_timings["total"].append(t_total_elapsed)

    def calc_stats(vals: List[float]) -> Dict[str, float]:
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        p50 = sorted_vals[int(0.50 * n)]
        p95 = sorted_vals[min(n - 1, int(0.95 * n))]
        mean_v = sum(sorted_vals) / n
        return {
            "median_p50_ms": round(p50, 3),
            "p95_ms": round(p95, 3),
            "mean_ms": round(mean_v, 3)
        }

    report = {
        "warmup_requests": warmup_count,
        "warm_benchmark_requests": benchmark_count,
        "stages": {
            "1_image_decode_preprocessing": calc_stats(stage_timings["1_decode"]),
            "2_face_detection_alignment": calc_stats(stage_timings["2_detection"]),
            "3_embedding_inference": calc_stats(stage_timings["3_inference"]),
            "4_vector_search_pgvector": calc_stats(stage_timings["4_vector_search"]),
            "5_serialization_response": calc_stats(stage_timings["5_serialization"]),
            "total_pipeline": calc_stats(stage_timings["total"])
        }
    }

    return report


if __name__ == "__main__":
    img_bytes = generate_profiling_image_bytes()
    res = profile_pipeline_stages(img_bytes, warmup_count=5, benchmark_count=20)
    import json
    print(json.dumps(res, indent=2))
