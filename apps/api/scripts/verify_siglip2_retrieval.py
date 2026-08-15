import io
import sys
import hashlib
from PIL import Image, ImageDraw

from app.services.recognition.siglip2 import SigLIP2RecognitionProvider
from app.repositories.celebrity_repository import CelebrityRepository


def create_test_portrait(color: tuple, pattern: str) -> bytes:
    """Generates synthetic portrait image bytes for verification testing."""
    img = Image.new("RGB", (224, 224), color=color)
    draw = ImageDraw.Draw(img)
    if pattern == "face_a":
        # Draw distinctive eye, nose, mouth positions for portrait A
        draw.ellipse([60, 70, 90, 100], fill=(255, 255, 255))
        draw.ellipse([130, 70, 160, 100], fill=(255, 255, 255))
        draw.polygon([(110, 100), (95, 140), (125, 140)], fill=(200, 100, 100))
        draw.rectangle([80, 160, 140, 180], fill=(220, 50, 50))
    else:
        # Draw distinctive eye, nose, mouth positions for portrait B
        draw.ellipse([50, 60, 80, 90], fill=(200, 200, 250))
        draw.ellipse([140, 60, 170, 90], fill=(200, 200, 250))
        draw.polygon([(110, 90), (100, 130), (120, 130)], fill=(100, 200, 100))
        draw.arc([70, 150, 150, 190], start=0, end=180, fill=(255, 255, 0), width=5)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def main():
    print("=== SigLIP 2 Image Retrieval Verification Script ===")
    provider = SigLIP2RecognitionProvider()

    # 1. Run provider self-test
    self_test_res = provider.self_test()
    print(f"SigLIP 2 Self Test: {self_test_res}")
    assert self_test_res["status"] == "PASSED", "SigLIP 2 self test failed!"

    # 2. Generate Image A and Image B
    bytes_a = create_test_portrait((180, 120, 90), "face_a")
    bytes_b = create_test_portrait((90, 150, 200), "face_b")

    hash_a = hashlib.md5(bytes_a).hexdigest()
    hash_b = hashlib.md5(bytes_b).hexdigest()
    print(f"\nImage A MD5 Hash: {hash_a}")
    print(f"Image B MD5 Hash: {hash_b}")
    assert hash_a != hash_b, "Test image hashes must be different!"
    print("[OK] VERIFIED: hashA != hashB")

    # 3. Align and extract SigLIP 2 embeddings
    aligned_a = provider.validate_and_align(bytes_a)
    aligned_b = provider.validate_and_align(bytes_b)

    emb_a = provider.generate_embedding(aligned_a)
    emb_b = provider.generate_embedding(aligned_b)

    print(f"\nEmbedding A (first 5 dims): {[round(x, 4) for x in emb_a[:5]]}")
    print(f"Embedding B (first 5 dims): {[round(x, 4) for x in emb_b[:5]]}")

    # Cosine Similarity between Embedding A and Embedding B
    dot_ab = sum(a * b for a, b in zip(emb_a, emb_b))
    print(f"Cosine Similarity (uA . uB): {round(dot_ab, 4)}")
    assert emb_a != emb_b, "Embeddings for different images must be different!"
    print("[OK] VERIFIED: embeddingA != embeddingB")

    # 4. Search reference index separately for Image A and Image B
    candidates_a = CelebrityRepository._get_standalone_mock_candidates(emb_a)
    candidates_b = CelebrityRepository._get_standalone_mock_candidates(emb_b)

    top_5_a = [(c[2].name, round(c[3], 4)) for c in candidates_a[:5]]
    top_5_b = [(c[2].name, round(c[3], 4)) for c in candidates_b[:5]]

    print("\nTop 5 Look-Alikes for Image A:")
    for rank, (name, dist) in enumerate(top_5_a, 1):
        print(f"  #{rank}: {name} (Cosine Dist: {dist})")

    print("\nTop 5 Look-Alikes for Image B:")
    for rank, (name, dist) in enumerate(top_5_b, 1):
        print(f"  #{rank}: {name} (Cosine Dist: {dist})")

    # 5. Assert distinct top candidate rankings
    top_name_a = top_5_a[0][0]
    top_name_b = top_5_b[0][0]
    print(f"\nTop #1 Candidate Image A: {top_name_a}")
    print(f"Top #1 Candidate Image B: {top_name_b}")

    assert top_5_a != top_5_b, "Top rankings for Image A and Image B must be different!"
    print("[OK] VERIFIED: Independent Retrieval Pipeline generates distinct top candidates for Image A vs. Image B")
    print("\n=== All Verification Checks Passed Successfully! ===")


if __name__ == "__main__":
    main()
