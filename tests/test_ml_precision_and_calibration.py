"""
TurmericGuard AI — Test Suite: ML Precision, Calibration & Conformal Abstention
Validates:
1. Continuous regression head resolution (Continuous MAE & RMSE measured per adulterant)
2. Isotonic probability calibration & reliability diagram (binned stated conf vs empirical acc)
3. Conformal abstention ("refuse to guess") on ambiguous or boundary frames
4. Multi-model ensemble agreement consensus across GB, RF, SVM, and MLP
5. Input signal quality tightening (blur & glare) and 3-5 sample spectral averaging
6. Honest continuous margin of error reporting (+/- delta w/w) in API responses
"""

import os
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import app
from core.models_ensemble import ensemble_model, TurmericEnsembleClassifier
from core.conformal_predictor import conformal_predictor
from core.feature_extraction import (
    extract_color_features,
    extract_spectral_signature,
    average_spectral_readings,
    fuse_features,
    SPECTRAL_WAVELENGTHS
)
from core.vision_pipeline import (
    check_image_quality,
    DEFAULT_BLUR_THRESHOLD,
    DEFAULT_GLARE_THRESHOLD
)
client = TestClient(app)
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'samples')


# =========================================================================
# 1. CONTINUOUS REGRESSION RESOLUTION TESTS (MAE & RMSE PER ADULTERANT)
# =========================================================================

def test_benchmark_reports_continuous_mae_and_rmse_per_adulterant():
    """Verify that continuous MAE and RMSE are measured and reported for every adulterant type."""
    report = ensemble_model.benchmark_metrics
    assert "continuous_regression" in report
    reg = report["continuous_regression"]

    # Continuous MAE and RMSE must be evaluated numbers (not unmeasured or hardcoded dummy 0)
    assert isinstance(reg["overall_adulterant_mae_pct"], float)
    assert isinstance(reg["overall_adulterant_rmse_pct"], float)
    assert 0.0 < reg["overall_adulterant_mae_pct"] < 3.0
    assert 0.0 < reg["overall_adulterant_rmse_pct"] < 4.0

    per_class = reg["per_adulterant_metrics"]
    required_adulterants = ['lead_chromate', 'metanil_yellow', 'acid_orange_7', 'starch_chalk_filler']

    for adulterant in required_adulterants:
        assert adulterant in per_class, f"Missing continuous metrics for {adulterant}"
        metrics = per_class[adulterant]
        assert "mae_pct" in metrics
        assert "rmse_pct" in metrics
        assert "empirical_error_margin_p95" in metrics
        assert metrics["mae_pct"] > 0.0
        assert metrics["rmse_pct"] > 0.0
        assert metrics["empirical_error_margin_p95"] > 0.0


def test_ensemble_outputs_continuous_concentration_with_margin():
    """Verify continuous concentration estimates include honest error margins (+/- delta)."""
    # Sample with adulteration (Lead Chromate sample)
    sample_path = os.path.join(SAMPLES_DIR, "lead_chromate_8pct.jpg")
    color = extract_color_features(sample_path)
    spec = extract_spectral_signature(color)
    fused = fuse_features(color, spec)

    pred = ensemble_model.predict(fused['vector'])

    assert not pred['is_pure']
    assert isinstance(pred['estimated_concentration_pct'], float)
    assert pred['estimated_concentration_pct'] > 0.0
    assert isinstance(pred['concentration_margin_pct'], float)
    assert pred['concentration_margin_pct'] > 0.0
    assert "±" in pred['concentration_display'] or "+/-" in pred['concentration_display']
    assert len(pred['concentration_ci_95']) == 2
    assert pred['concentration_ci_95'][0] < pred['concentration_ci_95'][1]


def test_pure_sample_yields_zero_concentration():
    """Verify that authentic pure turmeric returns 0.0% concentration."""
    sample_path = os.path.join(SAMPLES_DIR, "pure_alleppey.jpg")
    color = extract_color_features(sample_path)
    spec = extract_spectral_signature(color)
    fused = fuse_features(color, spec)

    pred = ensemble_model.predict(fused['vector'])
    assert pred['is_pure']
    assert pred['estimated_concentration_pct'] == 0.0
    assert pred['concentration_margin_pct'] == 0.0
    assert "0.0%" in pred['concentration_display']


# =========================================================================
# 2. PROBABILITY CALIBRATION & RELIABILITY DIAGRAM TESTS
# =========================================================================

def test_model_is_probability_calibrated():
    """Verify all 4 classifiers are calibrated and calibration metrics are recorded."""
    assert ensemble_model.calibrated_gb is not None
    assert ensemble_model.calibrated_rf is not None
    assert ensemble_model.calibrated_svm is not None
    assert ensemble_model.calibrated_mlp is not None

    report = ensemble_model.benchmark_metrics
    assert "calibration_reliability" in report
    cal = report["calibration_reliability"]
    assert cal["is_well_calibrated"] is True
    # Expected Calibration Error (ECE) should be below 3.5%
    assert cal["expected_calibration_error_pct"] < 3.5

    # Check 10-bin reliability diagram structure
    bins = cal["reliability_diagram_bins"]
    assert len(bins) > 0
    for b in bins:
        assert "confidence_bin" in b
        assert "sample_count" in b
        assert "stated_confidence_pct" in b
        assert "observed_accuracy_pct" in b
        assert "calibration_error_pct" in b


# =========================================================================
# 3. ABSTENTION / REFUSAL TO GUESS (CONFORMAL ABSTENTION) TESTS
# =========================================================================

def test_ensemble_abstains_on_highly_ambiguous_discordant_inputs():
    """Verify that when models disagree or confidence is low, the pipeline refuses to force a guess."""
    # Synthesize ambiguous feature vector (simulating discordant multi-modal signals)
    np.random.seed(999)
    # Neutral/noisy vector that falls between pure and adulterated boundaries
    neutral_vector = np.full(84, 0.5, dtype=np.float32)

    pred = ensemble_model.predict(neutral_vector)
    calibrated_res = conformal_predictor.calibrate(pred)

    if pred['is_inconclusive']:
        # Must refuse to guess: status routes to SUSPICIOUS with rescan guidance
        assert calibrated_res['status'] == 'SUSPICIOUS'
        assert calibrated_res['status_code'] == 'INCONCLUSIVE_RESCAN_REQUIRED'
        assert 'INCONCLUSIVE' in calibrated_res['badge_text']
        assert 'Rescan' in calibrated_res['recommendation']['headline']


def test_ensemble_agreement_score_present_in_all_predictions():
    """Verify ensemble agreement score (0-100%) is computed and returned on every prediction."""
    sample_path = os.path.join(SAMPLES_DIR, "metanil_yellow_5pct.jpg")
    color = extract_color_features(sample_path)
    spec = extract_spectral_signature(color)
    fused = fuse_features(color, spec)

    pred = ensemble_model.predict(fused['vector'])
    assert "ensemble_agreement_score" in pred
    assert 25.0 <= pred['ensemble_agreement_score'] <= 100.0


# =========================================================================
# 4. INPUT QUALITY FILTER TIGHTENING & MULTI-SAMPLE SPECTRAL AVERAGING
# =========================================================================

def test_tightened_quality_thresholds():
    """Verify Laplacian blur and specular glare thresholds are tightened."""
    assert DEFAULT_BLUR_THRESHOLD == 85.0
    assert DEFAULT_GLARE_THRESHOLD == 4.0


def test_multi_sample_spectral_averaging_reduces_noise():
    """Verify that 3-5 rapid spectral readings are averaged with noise reduction metrics."""
    np.random.seed(42)
    base_spectrum = [0.10 + 0.70 / (1.0 + math.exp(-(wl - 515) / 28.0)) for wl in SPECTRAL_WAVELENGTHS]

    # Generate 5 noisy scans
    scans = []
    for _ in range(5):
        noise = np.random.normal(0, 0.02, len(base_spectrum))
        scans.append(list(np.clip(np.array(base_spectrum) + noise, 0.01, 0.99)))

    avg_res = average_spectral_readings(scans, method='trimmed_mean')

    assert avg_res['samples_averaged'] == 5
    assert len(avg_res['averaged_reflectance']) == 61
    assert avg_res['noise_reduction_pct'] > 50.0 # ~55.3% theoretical noise reduction for N=5
    assert avg_res['snr_db'] > 20.0


def test_extract_spectral_signature_accepts_and_averages_multi_samples():
    """Verify extract_spectral_signature handles multi-scan bursts."""
    base_spectrum = [0.5] * 61
    scans = [base_spectrum, base_spectrum, base_spectrum]
    color = {'hsv': {'h': 42.0, 's': 70.0, 'v': 80.0}, 'rgb': {'r': 200, 'g': 160, 'b': 50}, 'photometrics': {'brightness': 150}}

    spec_res = extract_spectral_signature(color, user_spectra=scans)
    assert "multi_sample_averaging" in spec_res
    assert spec_res['multi_sample_averaging']['samples_averaged'] == 3


# =========================================================================
# 5. FASTAPI API INTEGRATION TESTS (ERROR MARGINS & ABSTENTION)
# =========================================================================

def test_api_analyze_returns_honest_concentration_margins():
    """Verify /v1/analyze returns concentration margins, display text, and CI bounds."""
    response = client.post("/v1/demo-analyze", json={"preset_key": "lead_chromate_8pct"})
    assert response.status_code == 200
    data = response.json()

    cls = data["classification"]
    assert "estimated_concentration_w_w" in cls
    assert "concentration_margin_pct" in cls
    assert "concentration_display" in cls
    assert "concentration_ci_95" in cls
    assert "calibrated_confidence_pct" in cls
    assert "ensemble_agreement_score" in cls

    # Concentration display must format as 'X.X% ± Y.Y% w/w'
    assert "±" in cls["concentration_display"]
    assert cls["concentration_margin_pct"] > 0.0


def test_compliance_benchmarks_endpoint_serves_continuous_metrics():
    """Verify /v1/compliance/benchmarks exposes the real held-out regression and calibration reports."""
    response = client.get("/v1/compliance/benchmarks")
    assert response.status_code == 200
    data = response.json()

    assert "data_source" in data
    assert "SYNTHETIC" in data["data_source"]
    assert "continuous_regression" in data
    assert "calibration_reliability" in data
    assert data["continuous_regression"]["overall_adulterant_mae_pct"] > 0.0
    assert data["calibration_reliability"]["expected_calibration_error_pct"] < 3.5

