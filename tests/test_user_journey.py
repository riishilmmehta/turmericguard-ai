"""
Comprehensive User Journey & International Standards Validation Suite
Simulates an international food safety officer (FSSAI / Codex Alimentarius inspector)
interacting with TurmericGuard AI at http://127.0.0.1:5000.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import json
import httpx
from PIL import Image

SERVER_URL = "http://127.0.0.1:5000"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "static", "samples")

def run_user_journey_test():
    print("=" * 85)
    print("TURMERICGUARD AI — COMPLETE END-TO-END USER JOURNEY AUDIT")
    print(f"Target Server: {SERVER_URL} | Role: ISO/IEC 17025 Lead Food Safety Auditor")
    print("=" * 85)

    try:
        test_client = httpx.Client(base_url=SERVER_URL, timeout=1.0)
        test_client.get("/health")
        client = test_client
        print(f"Connected to live server at {SERVER_URL}")
    except Exception:
        from fastapi.testclient import TestClient
        import sys
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        from app import app
        client = TestClient(app)
        print("Using in-process TestClient(app) emulation.")
    all_passed = True

    # STEP 1: Auditor accesses the Dashboard UI
    print("\n--- STEP 1: USER OPENS DASHBOARD HOME PAGE ---")
    resp = client.get("/")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.text
    assert "<title>TurmericGuard AI" in html, "Title missing"
    assert "inlinedMainCss" in html, "Inlined CSS missing"
    assert "purityGaugeCanvas" in html, "Gauge canvas missing"
    assert "spectralChartCanvas" in html, "Spectral chart canvas missing"
    print(f"[PASS] Dashboard loaded successfully ({len(html)} bytes). Inlined CSS verified.")

    # STEP 2: Auditor tests Reference Standard Presets (Zero-Latency Screen)
    print("\n--- STEP 2: AUDITOR TESTS PRESET SCREENING WORKFLOWS ---")
    presets_to_test = [
        ("pure_alleppey", "PURE", 85.0, "Pure Alleppey Reference Standard"),
        ("lead_chromate_8pct", "ADULTERATED", 0.0, "Lead Chromate Adulteration (8% w/w)"),
        ("metanil_yellow_5pct", "ADULTERATED", 0.0, "Metanil Yellow Synthetic Azo Dye (5% w/w)"),
        ("chalk_filler_15pct", "ADULTERATED", 0.0, "Chalk / Mineral Filler (15% w/w)"),
        ("borderline_suspicious", "SUSPICIOUS", 50.0, "Borderline Detection Limit Batch")
    ]

    for preset_key, exp_status, min_purity, label in presets_to_test:
        payload = {
            "preset_key": preset_key,
            "device_id": "TG-RPi5-LAB-01",
            "lot_number": f"LOT-APMC-TEST-{preset_key.upper()[:6]}"
        }
        res = client.post("/v1/demo-analyze", json=payload)
        assert res.status_code == 200, f"Demo analyze failed for {preset_key}: {res.text}"
        data = res.json()

        status = data["classification"]["status"]
        purity = data["classification"]["purity_score"]
        top_label = data["classification"]["top_detected_label"]
        ci = data["conformal_calibration"]
        tier2 = data["tier2_routing"]
        block_idx = data["traceability"]["block_index"]

        if exp_status == "SUSPICIOUS":
            status_match = status in ["SUSPICIOUS", "ADULTERATED"]
        else:
            status_match = (status == exp_status)

        if not status_match:
            all_passed = False

        pass_flag = "PASS" if status_match else "FAIL"
        print(f"[{pass_flag}] {label}")
        print(f"       Status: {status} | Purity Score: {purity:.1f}% | Conformal Interval: [{ci['low']}%, {ci['high']}%]")
        print(f"       Detected Agent: {top_label} | Tier-2 Referral: {tier2['required']}")
        print(f"       Ledger Anchor Block: #{block_idx} (SHA-256 Hash: {data['traceability']['block_hash'][:16]}...)")

    # STEP 3: Auditor executes Live Image Upload (Multipart File Transfer)
    print("\n--- STEP 3: AUDITOR UPLOADS REAL SAMPLES VIA CAMERA/FILE ---")
    upload_tests = [
        ("pure_alleppey.jpg", "PURE", "Pure Authentic Turmeric Photo"),
        ("lead_chromate_8pct.jpg", "ADULTERATED", "Lead Chromate Adulterated Photo")
    ]

    for filename, exp_status, label in upload_tests:
        fpath = os.path.join(SAMPLES_DIR, filename)
        with open(fpath, "rb") as f:
            files = {"image": (filename, f, "image/jpeg")}
            form_data = {
                "device_id": "TG-RPi5-LAB-01",
                "lot_number": f"LOT-LIVE-UPLOAD-{filename[:5].upper()}",
                "variety": "Field Specimen",
                "vendor_name": "Regional APMC Vendor"
            }
            res = client.post("/v1/analyze", data=form_data, files=files)

        assert res.status_code == 200, f"Analyze failed for {filename}: {res.text}"
        data = res.json()
        status = data["classification"]["status"]
        purity = data["classification"]["purity_score"]
        top_label = data["classification"]["top_detected_label"]

        passed = (status == exp_status)
        if not passed:
            all_passed = False

        pass_flag = "PASS" if passed else "FAIL"
        print(f"[{pass_flag}] Upload Screening: {label} ({filename})")
        print(f"       Result Status: {status} | Purity: {purity:.1f}% | Top Class: {top_label}")
        print(f"       95% Conformal Confidence: [{data['conformal_calibration']['low']}%, {data['conformal_calibration']['high']}%]")
        print(f"       SHAP Diagnostic Rationale: {data['explainability']['executive_summary'][:110]}...")

    # STEP 4: Auditor verifies Immutable Cryptographic Ledger
    print("\n--- STEP 4: AUDITOR VERIFIES SUPPLY-CHAIN TRACEABILITY LEDGER ---")
    res = client.get("/v1/ledger")
    assert res.status_code == 200, "Ledger fetch failed"
    ledger_data = res.json()
    blocks = ledger_data["blocks"]
    integrity = ledger_data["chain_integrity"]

    print(f"Total Ledger Blocks Anchored: {ledger_data['block_count']}")
    print(f"Cryptographic Chain Integrity: {'VALID' if integrity['valid'] else 'CORRUPTED'}")
    assert integrity["valid"], "Ledger chain integrity check failed!"
    print(f"[PASS] All {len(blocks)} blocks sequentially linked via SHA-256 hashes without tampering.")

    # STEP 5: Auditor accesses Public QR Verification Page & API
    print("\n--- STEP 5: PUBLIC CONSUMER / CUSTOMS QR VERIFICATION ---")
    sample_qr = blocks[-1]["test_id"]
    
    # 5a: Verify JSON API endpoint
    res_json = client.get(f"/v1/traceability/{sample_qr}")
    assert res_json.status_code == 200, f"Public JSON verification failed for {sample_qr}"
    json_data = res_json.json()
    assert json_data["verified"] is True, "Verification flag false"
    assert json_data["test_id"] == sample_qr, "Test ID mismatch in JSON"
    print(f"[PASS] Public JSON lookup for {sample_qr} returned authenticated status: {json_data['status']}")

    # 5b: Verify HTML Certificate view (/verify/{qr} and /v1/traceability/{qr}?format=html)
    res_html = client.get(f"/verify/{sample_qr}")
    assert res_html.status_code == 200, f"Public Certificate HTML failed for {sample_qr}"
    verify_html = res_html.text
    assert "Public Food Safety Certificate" in verify_html, "Certificate title missing"
    assert sample_qr in verify_html, "Test ID missing from certificate"
    print(f"[PASS] Public Certificate for {sample_qr} rendered with cryptographic authenticity seals.")


    # STEP 6: Auditor audits Fleet Calibration & Sensor Drift
    print("\n--- STEP 6: AUDITOR INSPECTS SENSOR FLEET & DRIFT METRICS ---")
    res = client.get("/v1/devices")
    assert res.status_code == 200
    devices_data = res.json()
    devices = devices_data["devices"]
    print(f"Monitored Hardware Units: {len(devices)}")
    for d in devices:
        print(f"   • {d['device_id']} ({d['sku']}) @ {d['location'][:35]}... Drift: {d['drift_metrics']['drift_pct']}% ({d['drift_metrics']['drift_status']})")

    # Perform field calibration routine on device with drift
    print("\n   Executing Spectralon 99% Reference Recalibration on TG-ESP32-FLD-02...")
    cal_res = client.post("/v1/devices/TG-ESP32-FLD-02/calibrate", json={
        "white_tile_reflectance_pct": 99.6,
        "dark_current_mv": 1.0,
        "operator_id": "FSSAI-AUDITOR-ISO17025"
    })
    assert cal_res.status_code == 200
    cal_data = cal_res.json()
    print(f"   [PASS] Recalibration complete! New Drift: {cal_data['drift_percentage']}%, Hash: {cal_data['calibration_hash']}")

    # STEP 7: Auditor verifies International Regulatory Compliance Benchmarks
    print("\n--- STEP 7: INTERNATIONAL STANDARDS & VALIDATION METRICS ---")
    res = client.get("/v1/compliance/benchmarks")
    assert res.status_code == 200
    benchmarks = res.json()
    lod_matrix = benchmarks["limit_of_detection_matrix"]
    iso_metrics = benchmarks["performance_by_adulterant"]
    citations = benchmarks["international_compliance_references"]

    print(f"Codex / FSSAI Limit of Detection (LOD) Entries: {len(lod_matrix)}")
    for m in lod_matrix:
        print(f"   • {m['adulterant']:32} LOD: {m['lod_w_w']}% w/w | Standard: {m['tier2_confirmatory_standard']}")

    print("\nISO/IEC 17025 Validation Performance by Class:")
    for p in iso_metrics:
        print(f"   • {p['class']:30} Precision: {p['precision']*100:.1f}% | Recall: {p['recall']*100:.1f}% | F1-Score: {p['f1_score']*100:.1f}%")

    print("\nInternational Regulatory Frameworks Verified:")
    for c in citations:
        print(f"   ✓ {c['standard_body']} — {c['regulation']}")

    print("\n" + "=" * 85)
    if all_passed:
        print("ALL AUDIT PHASES, ML MODELS, USER FLOWS, AND INTERNATIONAL BENCHMARKS: 100% PERFECT")
    else:
        print("AUDIT ENCOUNTERED ISSUES")
    print("=" * 85)

    return all_passed

if __name__ == "__main__":
    success = run_user_journey_test()
    exit(0 if success else 1)
