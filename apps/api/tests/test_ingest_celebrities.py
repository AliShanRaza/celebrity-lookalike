import csv
import json
import os
import pytest
from unittest.mock import MagicMock
from PIL import Image

from app.scripts.ingest_celebrities import CelebrityIngestionPipeline


@pytest.fixture
def temp_sample_image(tmp_path):
    """Creates a temporary 200x200 JPEG image on disk."""
    img_path = tmp_path / "sample_portrait.jpg"
    img = Image.new("RGB", (200, 200), color="red")
    img.save(img_path, format="JPEG")
    return str(img_path)


@pytest.fixture
def temp_manifest_json(tmp_path, temp_sample_image):
    """Creates a temporary JSON manifest file."""
    manifest_path = tmp_path / "manifest.json"
    data = [
        {
            "celebrity_name": "Test Actor",
            "gender": "male",
            "origin": "bollywood",
            "result_group": "A-List",
            "provenance": "Licensed Dataset",
            "image_path": temp_sample_image,
        }
    ]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return str(manifest_path)


@pytest.fixture
def temp_manifest_csv(tmp_path, temp_sample_image):
    """Creates a temporary CSV manifest file."""
    manifest_path = tmp_path / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["celebrity_name", "gender", "origin", "result_group", "provenance", "image_path"])
        writer.writeheader()
        writer.writerow({
            "celebrity_name": "Test Actress",
            "gender": "female",
            "origin": "hollywood",
            "result_group": "A-List",
            "provenance": "Licensed Dataset",
            "image_path": temp_sample_image,
        })
    return str(manifest_path)


def test_ingestion_dry_run_json(temp_manifest_json, tmp_path):
    mock_session = MagicMock()
    mock_execute_result = MagicMock()
    mock_execute_result.scalars().first.return_value = None
    mock_session.execute.return_value = mock_execute_result

    pipeline = CelebrityIngestionPipeline(session=mock_session, dry_run=True, model_ver="fake_v1")
    report_path = str(tmp_path / "report.csv")

    report_rows = pipeline.run(manifest_path=temp_manifest_json, report_out_path=report_path)

    assert len(report_rows) == 1
    assert report_rows[0]["status"] == "SUCCESS"
    assert report_rows[0]["quality_status"] == "PASSED_HIGH_QUALITY"
    assert report_rows[0]["dry_run"] is True
    assert os.path.exists(report_path)

    # Read CSV report
    with open(report_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["celebrity_name"] == "Test Actor"
        assert reader[0]["origin"] == "bollywood"
        assert reader[0]["status"] == "SUCCESS"


def test_ingestion_idempotency_skip(temp_manifest_json, tmp_path):
    mock_session = MagicMock()
    mock_execute_result = MagicMock()
    # Simulate existing record found in DB
    mock_execute_result.scalars().first.return_value = MagicMock()
    mock_session.execute.return_value = mock_execute_result

    pipeline = CelebrityIngestionPipeline(session=mock_session, dry_run=False, model_ver="fake_v1")
    report_path = str(tmp_path / "report.csv")

    report_rows = pipeline.run(manifest_path=temp_manifest_json, report_out_path=report_path)

    assert len(report_rows) == 1
    assert report_rows[0]["status"] == "SKIPPED"
    assert report_rows[0]["quality_status"] == "ALREADY_INGESTED"


def test_ingestion_file_not_found_error_report(tmp_path):
    manifest_path = tmp_path / "missing_file_manifest.json"
    data = [
        {
            "celebrity_name": "Ghost Celebrity",
            "gender": "male",
            "origin": "bollywood",
            "image_path": str(tmp_path / "non_existent_file.jpg"),
        }
    ]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    mock_session = MagicMock()
    mock_execute_result = MagicMock()
    mock_execute_result.scalars().first.return_value = None
    mock_session.execute.return_value = mock_execute_result

    pipeline = CelebrityIngestionPipeline(session=mock_session, dry_run=True)
    report_path = str(tmp_path / "error_report.csv")

    report_rows = pipeline.run(manifest_path=str(manifest_path), report_out_path=report_path)

    assert len(report_rows) == 1
    assert report_rows[0]["status"] == "FAILED"
    assert report_rows[0]["quality_status"] == "FILE_NOT_FOUND"
    assert "not found" in report_rows[0]["error_message"]


def test_ingestion_missing_origin_error_report(tmp_path, temp_sample_image):
    manifest_path = tmp_path / "missing_origin_manifest.json"
    data = [
        {
            "celebrity_name": "No Origin Celeb",
            "gender": "male",
            "image_path": temp_sample_image,
        }
    ]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    mock_session = MagicMock()
    pipeline = CelebrityIngestionPipeline(session=mock_session, dry_run=True)
    report_path = str(tmp_path / "origin_error_report.csv")

    report_rows = pipeline.run(manifest_path=str(manifest_path), report_out_path=report_path)

    assert len(report_rows) == 1
    assert report_rows[0]["status"] == "FAILED"
    assert report_rows[0]["quality_status"] == "INVALID_MANIFEST_ROW"
    assert report_rows[0]["error_code"] == "INVALID_MANIFEST_ROW"
    assert "origin" in report_rows[0]["error_message"]
