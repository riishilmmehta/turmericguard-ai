"""
TurmericGuard AI — Out-of-Distribution (OOD) Gate & Gallery Import Test Suite
Validates:
1. Immediate Heuristic Pre-Filter (HSV hue 10°-88°, saturation >= 12%, CIELAB b* >= 8.0, red/blue ratio)
2. Trained Machine Learning OOD Classifier (Random Forest + Isolation Forest)
3. Zero-Hallucination & Conformal Prediction Suppression on Non-Turmeric Inputs
4. Choose from Gallery Option with Strict Quality and Dominant Mound Checks
5. Provenance Metadata Tracking (capture_source: live_camera vs gallery_import in Results & Ledger)
6. Model Validation Checklist compliance (non_turmeric_rejection_test)
"""

import os
import sys
import io
import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app import app
from core.ood_detector import ood_detector, check_heuristic_turmeric, TurmericOODClassifier
from core.feature_extraction import extract_color_features
from core.vision_pipeline import execute_vision_pipeline
from core.traceability_ledger import traceability_ledger
from core.dataset_benchmark import CURATED_DEMO_PRESETS
from core.models_ensemble import ensemble_model

client = TestClient(app)
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'samples')


# =========================================================================
# 1. IMMEDIATE HEURISTIC & DIVERSE OBJECT REJECTION TESTS
# =========================================================================

def test_heuristic_rejects_blue_stapler():
    """Verify blue objects (staplers, jeans, blue plastics) are immediately rejected."""
    blue_features = {
        'image_valid': True,
        'rgb': {'r': 25.0, 'g': 70.0, 'b': 210.0, 'rg_ratio': 0.36, 'rb_ratio': 0.12, 'gb_ratio': 0.33},
        'hsv': {'h': 225.0, 's': 88.0, 'v': 82.0},
        'photometrics': {'brightness': 72.0}
    }
    is_ok, reason = check_heuristic_turmeric(blue_features)
    assert is_ok is False
    assert ("chromaticity" in reason.lower() or "blue channel" in reason.lower() or "outside turmeric" in reason.lower())


def test_heuristic_rejects_green_leaves():
    """Verify green foliage, vegetables, and matcha are rejected due to negative a* / green hue."""
    green_features = {
        'image_valid': True,
        'rgb': {'r': 40.0, 'g': 165.0, 'b': 45.0, 'rg_ratio': 0.24, 'rb_ratio': 0.89, 'gb_ratio': 3.67},
        'hsv': {'h': 122.0, 's': 75.0, 'v': 64.0},
        'photometrics': {'brightness': 114.0}
    }
    cielab = {'L_star': 58.0, 'a_star': -28.0, 'b_star': 35.0}
    is_ok, reason = check_heuristic_turmeric(green_features, cielab=cielab)
    assert is_ok is False
    assert "green hue detected" in reason.lower() or "outside turmeric" in reason.lower()


def test_heuristic_rejects_white_copy_paper():
    """Verify achromatic white surfaces (paper, desk, sugar, salt) are rejected for low saturation."""
    white_features = {
        'image_valid': True,
        'rgb': {'r': 245.0, 'g': 244.0, 'b': 246.0, 'rg_ratio': 1.0, 'rb_ratio': 1.0, 'gb_ratio': 1.0},
        'hsv': {'h': 240.0, 's': 1.5, 'v': 96.0},
        'photometrics': {'brightness': 245.0}
    }
    is_ok, reason = check_heuristic_turmeric(white_features)
    assert is_ok is False
    assert "desaturated" in reason.lower() or "chromaticity" in reason.lower()


def test_heuristic_rejects_dark_surfaces_and_shadows():
    """Verify dark countertops, floors, and heavy shadows are rejected for insufficient illuminance."""
    dark_features = {
        'image_valid': True,
        'rgb': {'r': 14.0, 'g': 12.0, 'b': 10.0, 'rg_ratio': 1.16, 'rb_ratio': 1.4, 'gb_ratio': 1.2},
        'hsv': {'h': 30.0, 's': 28.0, 'v': 5.5},
        'photometrics': {'brightness': 12.0}
    }
    is_ok, reason = check_heuristic_turmeric(dark_features)
    assert is_ok is False
    assert "too dark" in reason.lower() or "chromaticity" in reason.lower()


def test_heuristic_accepts_pure_turmeric():
    """Verify genuine pure turmeric powder satisfies physical envelope."""
    pure_features = {
        'image_valid': True,
        'rgb': {'r': 212.0, 'g': 168.0, 'b': 45.0, 'rg_ratio': 1.26, 'rb_ratio': 4.71, 'gb_ratio': 3.73},
        'hsv': {'h': 44.0, 's': 78.5, 'v': 83.1},
        'photometrics': {'brightness': 167.0}
    }
    cielab = {'L_star': 71.0, 'a_star': 12.5, 'b_star': 68.2}
    is_ok, reason = check_heuristic_turmeric(pure_features, cielab=cielab)
    assert is_ok is True
    assert reason is None


# =========================================================================
# 2. TRAINED ML OOD CLASSIFIER & SYNTHETIC NEGATIVE TESTS
# =========================================================================

def test_trained_ood_classifier_rejects_non_turmeric_sample():
    """Verify the trained binary classifier & anomaly detector reject non_turmeric_sample.jpg."""
    sample_path = os.path.join(SAMPLES_DIR, 'non_turmeric_sample.jpg')
    assert os.path.exists(sample_path), "non_turmeric_sample.jpg must exist"

    img = Image.open(sample_path).convert('RGB')
    color_features = extract_color_features(img)
    res = ood_detector.evaluate(color_features, capture_source="live_camera")

    assert res['is_turmeric'] is False
    assert res['rejection_message'] == "This doesn't look like turmeric powder. Please scan a turmeric sample."
    assert res['supporting_text'] == "Make sure the sample fills the guide box and is turmeric powder."


def test_trained_ood_classifier_accepts_authentic_alleppey():
    """Verify that certified pure turmeric sample passes the OOD gate."""
    sample_path = os.path.join(SAMPLES_DIR, 'pure_alleppey.jpg')
    img = Image.open(sample_path).convert('RGB')
    vision_res = execute_vision_pipeline(img)

    if vision_res['roi']['detected_mound']:
        mound_pil = Image.fromarray(vision_res['roi']['cropped_rgb'])
        color_features = extract_color_features(mound_pil)
    else:
        color_features = extract_color_features(img)

    res = ood_detector.evaluate(
        color_features=color_features,
        cielab=vision_res['cielab_normalization'],
        precomputed_vision=vision_res,
        capture_source="live_camera"
    )

    assert res['is_turmeric'] is True
    assert res['rejection_code'] is None
    assert res['ood_score'] >= 0.50


# =========================================================================
# 3. CONFORMAL PREDICTION & CONTAMINATION SUPPRESSION VIA API
# =========================================================================

def test_analyze_endpoint_ood_rejection_suppresses_confidence_and_contamination():
    """
    CRITICAL REQUIREMENT:
    When non-turmeric is submitted to /v1/analyze:
    - HTTP 422 returned
    - is_turmeric == False
    - error == 'OOD_REJECTION'
    - NO contamination number returned
    - NO confidence score returned
    - Conformal prediction badge completely omitted
    """
    sample_path = os.path.join(SAMPLES_DIR, 'non_turmeric_sample.jpg')
    with open(sample_path, 'rb') as f:
        file_bytes = f.read()

    response = client.post(
        "/v1/analyze",
        files={"image": ("non_turmeric.jpg", file_bytes, "image/jpeg")},
        data={"device_id": "TG-RPi5-LAB-01", "capture_source": "live_camera"}
    )

    assert response.status_code == 422
    data = response.json()

    assert data["is_turmeric"] is False
    assert data["error"] == "OOD_REJECTION"
    assert data["message"] == "This doesn't look like turmeric powder. Please scan a turmeric sample."
    assert data["supporting_text"] == "Make sure the sample fills the guide box and is turmeric powder."

    # Verify zero hallucination of purity, contamination, or conformal predictions
    assert data["classification"] is None, "Classification head must be suppressed on OOD rejection!"
    assert data["conformal_calibration"] is None, "Conformal prediction intervals must be completely suppressed!"
    assert data["edge_inference"] is None, "Edge inference head must be suppressed on OOD rejection!"


def test_demo_analyze_non_turmeric_preset_rejection():
    """Verify demo-analyze with non_turmeric_object preset triggers OOD rejection with zero confidence metrics."""
    response = client.post(
        "/v1/demo-analyze",
        json={"preset_key": "non_turmeric_object", "device_id": "TG-RPi5-LAB-01"}
    )

    assert response.status_code == 422
    data = response.json()

    assert data["is_turmeric"] is False
    assert data["error"] == "OOD_REJECTION"
    assert data["message"] == "This doesn't look like turmeric powder. Please scan a turmeric sample."
    assert data["classification"] is None
    assert data["conformal_calibration"] is None


def test_edge_predict_endpoint_ood_rejection():
    """Verify /v1/edge/predict rejects non-turmeric inputs with HTTP 422 and REJECTED_NON_TURMERIC."""
    sample_path = os.path.join(SAMPLES_DIR, 'non_turmeric_sample.jpg')
    with open(sample_path, 'rb') as f:
        file_bytes = f.read()

    response = client.post(
        "/v1/edge/predict",
        files={"image": ("sample.jpg", file_bytes, "image/jpeg")},
        data={"capture_source": "live_camera"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["is_turmeric"] is False
    assert data["verdict"] == "REJECTED_NON_TURMERIC"
    assert data["message"] == "This doesn't look like turmeric powder. Please scan a turmeric sample."


# =========================================================================
# 4. CHOOSE FROM GALLERY OPTION & STRICTER MOUND PRESENCE
# =========================================================================

def test_gallery_import_requires_dominant_powder_mound():
    """
    Gallery images must have a clear, dominant single powder mound.
    If an image lacks a clear powder contour (e.g. multi-object, meme, screenshot),
    it fails gracefully into the OOD rejection state.
    """
    # Create synthetic multi-object / flat checkerboard image with no mound
    flat_arr = np.zeros((300, 300, 3), dtype=np.uint8)
    flat_arr[:150, :150] = [200, 160, 40]
    flat_arr[150:, 150:] = [200, 160, 40]
    flat_img = Image.fromarray(flat_arr)

    # Force precomputed vision with detected_mound = False
    mock_vision = {
        'roi': {
            'detected_mound': False,
            'contour_meta': {'foreground_coverage_pct': 1.2}
        }
    }
    color_features = extract_color_features(flat_img)

    res = ood_detector.evaluate(
        color_features=color_features,
        precomputed_vision=mock_vision,
        capture_source="gallery_import"
    )

    assert res['is_turmeric'] is False
    assert res['rejection_code'] == "NO_DOMINANT_SAMPLE_MOUND"
    assert res['rejection_message'] == "This doesn't look like turmeric powder. Please scan a turmeric sample."


def test_gallery_import_valid_sample_passes():
    """Verify valid turmeric image imported via gallery passes full pipeline with capture_source='gallery_import'."""
    sample_path = os.path.join(SAMPLES_DIR, 'pure_alleppey.jpg')
    with open(sample_path, 'rb') as f:
        file_bytes = f.read()

    response = client.post(
        "/v1/analyze",
        files={"image": ("gallery_alleppey.jpg", file_bytes, "image/jpeg")},
        data={
            "device_id": "TG-RPi5-LAB-01",
            "capture_source": "gallery_import",
            "lot_number": "LOT-GALLERY-TEST"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["is_turmeric"] is True
    assert data["capture_source"] == "gallery_import"
    assert data["classification"]["status"] == "PURE"
    assert data["classification"]["estimated_concentration_w_w"] == 0.0
    assert data["conformal_calibration"] is not None


# =========================================================================
# 5. METADATA PROVENANCE & LEDGER TRACKING
# =========================================================================

def test_provenance_metadata_recorded_in_traceability_ledger():
    """Verify that capture_source is stored in the append-only ledger block."""
    initial_chain_len = len(traceability_ledger.chain)

    # 1. Live camera analysis
    sample_path = os.path.join(SAMPLES_DIR, 'lead_chromate_8pct.jpg')
    with open(sample_path, 'rb') as f:
        file_bytes = f.read()

    res_live = client.post(
        "/v1/analyze",
        files={"image": ("live_cam.jpg", file_bytes, "image/jpeg")},
        data={"capture_source": "live_camera", "lot_number": "LOT-PROV-LIVE"}
    )
    assert res_live.status_code == 200
    block_live = traceability_ledger.chain[-1]
    assert getattr(block_live, 'capture_source', None) == "live_camera"

    # 2. Gallery import analysis
    res_gallery = client.post(
        "/v1/analyze",
        files={"image": ("gallery_pick.jpg", file_bytes, "image/jpeg")},
        data={"capture_source": "gallery_import", "lot_number": "LOT-PROV-GALLERY"}
    )
    assert res_gallery.status_code == 200
    block_gallery = traceability_ledger.chain[-1]
    assert getattr(block_gallery, 'capture_source', None) == "gallery_import"


# =========================================================================
# 6. MODEL VALIDATION CHECKLIST COMPLIANCE & FRONTEND INTEGRITY
# =========================================================================

def test_benchmark_report_contains_non_turmeric_rejection_test():
    """Verify the formal ISO/IEC 17025 benchmark matrix contains non_turmeric_rejection_test in robustness."""
    checklist = ensemble_model.benchmark_metrics.get("model_validation_checklist", {})
    robustness = checklist.get("robustness", {})
    assert "non_turmeric_rejection_test" in robustness, "Must contain non_turmeric_rejection_test!"
    test_entry = robustness["non_turmeric_rejection_test"]
    assert test_entry["status"] == "PASS"
    assert test_entry["samples_evaluated"] >= 50
    assert test_entry["rejection_accuracy_pct"] == 100.0


def test_frontend_shutter_captures_real_camera_canvas_and_sends_to_analyze():
    """Verify index.html and templates/index.html capture real camera canvas to /v1/analyze."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for filename in ['index.html', os.path.join('templates', 'index.html')]:
        filepath = os.path.join(root_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Shutter scan MUST capture from video canvas or toggle camera
        assert "canvas.getContext('2d')" in content, f"{filename} missing canvas context extraction!"
        assert "ctx.drawImage(video" in content, f"{filename} missing video frame drawing to canvas!"
        assert "sendImageForAnalysis" in content, f"{filename} missing sendImageForAnalysis function!"
        assert "/v1/analyze" in content, f"{filename} missing /v1/analyze endpoint target!"
        assert "fetch(" in content, f"{filename} missing fetch call!"
        assert "OOD_REJECTION" in content, f"{filename} missing OOD_REJECTION handling!"
        assert "oodRejectionContainer" in content, f"{filename} missing oodRejectionContainer element!"


def test_react_native_edge_service_rejects_missing_image_without_hallucinating():
    """Verify EdgeInferenceService.js rejects missing images rather than returning pure turmeric."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service_path = os.path.join(root_dir, 'mobile_app', 'react_native', 'src', 'services', 'EdgeInferenceService.js')
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "if (!imageUri && !options.presetId)" in content, "Missing null imageUri rejection guard!"
    assert "NO_IMAGE_PROVIDED" in content, "Missing NO_IMAGE_PROVIDED error code!"


def test_gallery_path_includes_client_side_ood_inspection():
    """Verify both index.html and templates/index.html run client-side OOD inspection on gallery imports."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for filename in ['index.html', os.path.join('templates', 'index.html')]:
        filepath = os.path.join(root_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "confirmGalleryAnalysis" in content, f"{filename} missing confirmGalleryAnalysis!"
        assert "inspectCanvasForTurmeric(offscreenCanvas)" in content, f"{filename} missing client-side OOD check on gallery path!"
        assert "backendUnavailableContainer" in content, f"{filename} missing backendUnavailableContainer!"
        assert "demoSimulationBanner" in content, f"{filename} missing demoSimulationBanner!"


def test_mobile_apps_visibly_label_demo_presets():
    """Verify React Native and Flutter mobile apps visibly label preset data as illustrative."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rn_service = os.path.join(root_dir, 'mobile_app', 'react_native', 'src', 'services', 'EdgeInferenceService.js')
    rn_dash = os.path.join(root_dir, 'mobile_app', 'react_native', 'src', 'components', 'VerificationDashboard.js')
    flutter_cam = os.path.join(root_dir, 'mobile_app', 'flutter', 'lib', 'screens', 'camera_screen.dart')
    flutter_dash = os.path.join(root_dir, 'mobile_app', 'flutter', 'lib', 'screens', 'verification_dashboard.dart')

    with open(rn_service, 'r', encoding='utf-8') as f:
        rn_s_code = f.read()
    assert "is_demo_preset: true" in rn_s_code
    assert "Demo Preset (Illustrative)" in rn_s_code

    with open(rn_dash, 'r', encoding='utf-8') as f:
        rn_d_code = f.read()
    assert "demoPresetBanner" in rn_d_code
    assert "Demo preset only" in rn_d_code

    with open(flutter_cam, 'r', encoding='utf-8') as f:
        fl_c_code = f.read()
    assert "'is_demo_preset': true" in fl_c_code

    with open(flutter_dash, 'r', encoding='utf-8') as f:
        fl_d_code = f.read()
    assert "Demo preset only" in fl_d_code

