"""
TurmericGuard AI — Test Suite
Validates Section 7.2 API endpoints, feature extraction, conformal intervals,
explainability attributions, and hash chain ledger integrity.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app import app
from core.traceability_ledger import traceability_ledger

client = TestClient(app)


def test_dashboard_renders():
    """Verify web dashboard HTML endpoint returns 200 with required UI elements."""
    response = client.get("/")
    assert response.status_code == 200
    assert "TurmericGuard AI" in response.text
    assert "Optical Sensing Chamber" in response.text
    assert "Traceability Ledger" in response.text


def test_demo_analyze_pure_sample():
    """Verify demo screening on pure authentic Alleppey sample."""
    payload = {
        "preset_key": "pure_alleppey",
        "device_id": "TG-RPi5-LAB-01",
        "lot_number": "LOT-TEST-PURE-01"
    }
    response = client.post("/v1/demo-analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["classification"]["status"] == "PURE"
    assert data["classification"]["purity_score"] >= 85.0
    assert data["conformal_calibration"]["confidence_level"] == "95%"
    assert "traceability" in data
    assert data["traceability"]["tamper_evident"] is True
    assert "explainability" in data
    assert len(data["explainability"]["top_attributions"]) > 0


def test_demo_analyze_lead_chromate():
    """Verify detection of hazardous Lead Chromate (PbCrO4) pigment."""
    payload = {
        "preset_key": "lead_chromate_8pct",
        "device_id": "TG-RPi5-LAB-01",
        "lot_number": "LOT-TEST-LEAD-01"
    }
    response = client.post("/v1/demo-analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["classification"]["status"] == "ADULTERATED"
    assert data["classification"]["top_detected_class"] == "lead_chromate"
    assert data["tier2_routing"]["required"] is True
    assert "LA-ICP-MS" in data["tier2_routing"]["confirmatory_method"]
    assert "FSSAI" in data["recommendation"]["regulatory_status"]


def test_demo_analyze_metanil_yellow():
    """Verify detection of banned synthetic azo dye Metanil Yellow."""
    payload = {
        "preset_key": "metanil_yellow_5pct",
        "device_id": "TG-ESP32-FLD-01",
        "lot_number": "LOT-TEST-MY-01"
    }
    response = client.post("/v1/demo-analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["classification"]["status"] == "ADULTERATED"
    assert data["classification"]["top_detected_class"] == "metanil_yellow"
    assert data["tier2_routing"]["required"] is True


def test_get_history_endpoint():
    """Verify GET /v1/history returns paginated test records."""
    response = client.get("/v1/history?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert "total_count" in data
    assert data["total_count"] > 0


def test_device_drift_monitoring():
    """Verify GET /v1/devices/{id}/drift returns optical drift metrics."""
    response = client.get("/v1/devices/TG-RPi5-LAB-01/drift")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "TG-RPi5-LAB-01"
    assert "drift_pct" in data
    assert "calibration_state" in data


def test_device_calibration_event():
    """Verify POST /v1/devices/{id}/calibrate logs calibration event."""
    payload = {
        "white_tile_reflectance_pct": 99.5,
        "dark_current_mv": 1.1,
        "operator_id": "TEST-OPERATOR"
    }
    response = client.post("/v1/devices/TG-RPi5-LAB-01/calibrate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "calibration_hash" in data
    assert data["drift_percentage"] <= 1.0


def test_traceability_ledger_integrity():
    """Verify GET /v1/ledger and cryptographic hash-chain integrity."""
    response = client.get("/v1/ledger")
    assert response.status_code == 200
    data = response.json()
    assert data["chain_integrity"]["valid"] is True
    assert data["block_count"] >= 3


def test_public_qr_verification_lookup():
    """Verify GET /v1/traceability/{qr_code} public lookup."""
    # Lookup genesis or seeded block
    response = client.get("/v1/traceability/TG-20261028-1042")
    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert "cryptographic_block_hash" in data
    assert "testing_station" in data


def test_compliance_benchmarks_endpoint():
    """Verify GET /v1/compliance/benchmarks returns LOD and confusion matrix."""
    response = client.get("/v1/compliance/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_accuracy"] >= 90.0
    assert len(data["limit_of_detection_matrix"]) == 4
    assert "confusion_matrix" in data
