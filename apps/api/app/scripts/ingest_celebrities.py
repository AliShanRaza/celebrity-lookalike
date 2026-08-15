import argparse
import csv
import json
import os
import sys
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import SessionLocal
from app.models.celebrity import Celebrity
from app.models.celebrity_image import CelebrityImage
from app.models.celebrity_embedding import CelebrityEmbedding
from app.services.image_intake import SecureImageIntakeService
from app.services.recognition import get_recognition_provider, FaceDetectionError
from app.repositories.celebrity_repository import CelebrityRepository

logger = logging.getLogger("ingest_celebrities")


class CelebrityIngestionPipeline:
    """
    Offline celebrity ingestion pipeline for bulk populating celebrity metadata,
    reference images, and vector embeddings into PostgreSQL + pgvector.
    Supports resumability, idempotency, quality status logging, error report CSV generation,
    and dry-run execution mode.
    """

    def __init__(self, session: Session, dry_run: bool = False, model_ver: str | None = None):
        self.session = session
        self.dry_run = dry_run
        self.provider = get_recognition_provider()
        self.model_version = model_ver or self.provider.model_version

    def load_manifest(self, manifest_path: str) -> List[Dict[str, Any]]:
        """Loads CSV or JSON manifest file containing celebrity image records."""
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest file not found at path: {manifest_path}")

        records = []
        if manifest_path.lower().endswith(".json"):
            with open(manifest_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        else:
            with open(manifest_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                records = list(reader)
        return records

    def is_already_ingested(self, celebrity_name: str, image_url_or_path: str) -> bool:
        """
        Idempotency check: verifies if an embedding for this celebrity + image + model_version already exists.
        """
        stmt = (
            select(CelebrityEmbedding)
            .join(CelebrityImage, CelebrityEmbedding.celebrity_image_id == CelebrityImage.id)
            .join(Celebrity, CelebrityEmbedding.celebrity_id == Celebrity.id)
            .where(
                Celebrity.name == celebrity_name,
                CelebrityImage.image_url == image_url_or_path,
                CelebrityEmbedding.model_version == self.model_version
            )
        )
        existing = self.session.execute(stmt).scalars().first()
        return existing is not None

    def process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a single celebrity image manifest row."""
        celebrity_name = (record.get("name") or record.get("celebrity_name") or "").strip()
        gender = (record.get("gender") or "male").strip().lower()
        origin = (record.get("origin") or "").strip().lower()
        bio = (record.get("bio") or "").strip() or None
        result_group = (record.get("result_group") or "").strip()
        provenance = (record.get("provenance") or record.get("image_source") or "").strip()
        licence_text = (record.get("licence_text") or record.get("license_text") or record.get("license") or "").strip() or None
        attribution = (record.get("attribution") or record.get("credit") or "").strip() or None
        image_path = (record.get("image_path") or record.get("local_path") or "").strip()

        report_item = {
            "celebrity_name": celebrity_name,
            "gender": gender,
            "origin": origin,
            "result_group": result_group,
            "provenance": provenance,
            "licence_text": licence_text or "",
            "attribution": attribution or "",
            "image_path": image_path,
            "model_version": self.model_version,
            "status": "PENDING",
            "quality_status": "UNKNOWN",
            "error_code": "",
            "error_message": "",
            "celebrity_id": "",
            "embedding_id": "",
            "dry_run": self.dry_run,
        }

        if not celebrity_name or not image_path or not origin:
            report_item["status"] = "FAILED"
            report_item["quality_status"] = "INVALID_MANIFEST_ROW"
            report_item["error_code"] = "INVALID_MANIFEST_ROW"
            report_item["error_message"] = "Missing required celebrity_name, image_path, or origin field in manifest"
            return report_item

        # 1. Idempotency Check
        if self.is_already_ingested(celebrity_name, image_path):
            report_item["status"] = "SKIPPED"
            report_item["quality_status"] = "ALREADY_INGESTED"
            report_item["error_message"] = f"Record already ingested for model_version '{self.model_version}'"
            return report_item

        # 2. Local File Existence Check
        resolved_path = image_path
        if not os.path.exists(resolved_path):
            alt_path = os.path.join(os.getcwd(), image_path)
            if os.path.exists(alt_path):
                resolved_path = alt_path
            else:
                folder_name = os.path.basename(os.path.dirname(image_path))
                img_file = os.path.basename(image_path)
                data_img_dir = os.path.join(os.getcwd(), "data", "images")
                if os.path.exists(data_img_dir):
                    subdirs = os.listdir(data_img_dir)
                    for sd in subdirs:
                        if sd.encode("ascii", "ignore") == folder_name.encode("ascii", "ignore"):
                            candidate = os.path.join(data_img_dir, sd, img_file)
                            if os.path.exists(candidate):
                                resolved_path = candidate
                                break

        if not os.path.exists(resolved_path):
            report_item["status"] = "FAILED"
            report_item["quality_status"] = "FILE_NOT_FOUND"
            report_item["error_code"] = "FILE_NOT_FOUND"
            report_item["error_message"] = f"Image file not found at path '{image_path}'"
            return report_item

        image_path = resolved_path

        try:
            # 3. Read raw image bytes
            with open(image_path, "rb") as f:
                raw_bytes = f.read()

            # 4. Secure Image Intake Validation & RGB Normalization
            processed_bytes, _ = SecureImageIntakeService.process_image_bytes(
                raw_bytes, filename_hint=os.path.basename(image_path)
            )

            # 5. Face Detection & Landmark Alignment (enforces exactly 1 face)
            aligned_crop_bytes = self.provider.validate_and_align(processed_bytes)

            # 6. Embedding Inference (L2 Normalized)
            embedding_vector = self.provider.generate_embedding(aligned_crop_bytes)

            report_item["quality_status"] = "PASSED_HIGH_QUALITY"

            # 7. Persistence (Skipped if dry_run)
            if not self.dry_run:
                # Find or create Celebrity record
                stmt_celeb = select(Celebrity).where(Celebrity.name == celebrity_name)
                celeb = self.session.execute(stmt_celeb).scalars().first()
                if not celeb:
                    celeb = CelebrityRepository.create_celebrity(
                        self.session, name=celebrity_name, gender=gender, origin=origin, bio=bio
                    )

                # Create CelebrityImage record
                celeb_img = CelebrityRepository.create_celebrity_image(
                    self.session,
                    celebrity_id=celeb.id,
                    image_url=image_path,
                    licence_text=licence_text,
                    attribution=attribution
                )

                # Create CelebrityEmbedding record
                emb = CelebrityRepository.create_celebrity_embedding(
                    self.session,
                    celebrity_id=celeb.id,
                    celebrity_image_id=celeb_img.id,
                    embedding=embedding_vector,
                    model_version=self.model_version
                )

                self.session.commit()
                report_item["celebrity_id"] = str(celeb.id)
                report_item["embedding_id"] = str(emb.id)

            report_item["status"] = "SUCCESS"

        except FaceDetectionError as fde:
            report_item["status"] = "FAILED"
            report_item["quality_status"] = fde.error_code
            report_item["error_code"] = fde.error_code
            report_item["error_message"] = fde.message
        except Exception as exc:
            report_item["status"] = "FAILED"
            report_item["quality_status"] = "UNEXPECTED_ERROR"
            report_item["error_code"] = "UNEXPECTED_ERROR"
            report_item["error_message"] = str(exc)

        return report_item

    def run(self, manifest_path: str, report_out_path: str = "ingestion_report.csv") -> List[Dict[str, Any]]:
        records = self.load_manifest(manifest_path)
        report_rows = []

        logger.info(f"Starting ingestion pipeline for {len(records)} records (dry_run={self.dry_run})...")

        for record in records:
            report_item = self.process_record(record)
            report_rows.append(report_item)

        # Write ingestion report CSV (never silently skip errors)
        fieldnames = [
            "celebrity_name", "gender", "origin", "result_group", "provenance", "licence_text", "attribution", "image_path",
            "model_version", "status", "quality_status", "error_code", "error_message",
            "celebrity_id", "embedding_id", "dry_run"
        ]

        with open(report_out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_rows)

        logger.info(f"Ingestion pipeline finished. Report output to '{report_out_path}'.")
        return report_rows


def main():
    parser = argparse.ArgumentParser(description="Offline Celebrity Ingestion Pipeline")
    parser.add_argument("--manifest", required=True, help="Path to input CSV or JSON manifest file")
    parser.add_argument("--report-out", default="ingestion_report.csv", help="Path to output report CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Run validation and embedding extraction without DB commits")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    try:
        db = SessionLocal()
    except Exception as exc:
        logger.error(f"Database connection failed during startup: {exc}")
        sys.exit(1)

    try:
        pipeline = CelebrityIngestionPipeline(session=db, dry_run=args.dry_run)
        pipeline.run(manifest_path=args.manifest, report_out_path=args.report_out)
    finally:
        db.close()


if __name__ == "__main__":
    main()
