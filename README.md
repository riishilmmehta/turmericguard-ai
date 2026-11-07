# TurmericGuard AI — International Food Safety Screening Platform

> **Codename**: TurmericGuard AI  
> **Mission**: On-Site Screening of Lead Chromate and Synthetic Dye Adulteration in Turmeric Powder Using Multi-Modal Sensing, Machine Learning, Conformal Prediction, and Cryptographic Traceability.  
> **Benchmark Standards**: Codex Alimentarius CXS 193-1995 · FSSAI Spices Regulations 2011 · ISO/IEC 17025 Ready

---

## 1. Overview & Vision

Turmeric's high market value and distinct yellow color create strong economic incentives for adulteration with hazardous industrial pigments such as **Lead Chromate (PbCrO₄)**—a potent neurotoxin with zero safe intake level—along with synthetic azo dyes (**Metanil Yellow**, **Acid Orange 7**) and inert fillers (**chalk, starch, soapstone**). 

**TurmericGuard AI** bridges the gap between slow, costly confirmatory laboratories (ICP-MS, HPLC) and crude, operator-dependent home tests (FSSAI DART manual). It delivers a calibrated, quantitative, tamper-evident screening instrument operating in **under 30 seconds** without requiring specialized lab equipment.

---

## 2. System Architecture

```
[ LAYER 1: SENSING HARDWARE ]
  - 12MP Camera (Fixed Distance, Controlled 5000–6500K LED Ring Enclosure)
  - AS7265x Tri-Spectral / Vis-SWNIR Spectrometer (400–1000 nm, 61 bands)
  - Certified White Reference Tile (Spectralon 99% calibration standard)
      │
      ▼
[ LAYER 2: EDGE PROCESSING & CALIBRATION ]
  - Raspberry Pi 4/5 (Lab-grade unit) / ESP32 (Battery-powered field unit)
  - Automatic white-balance correction & optical baseline normalization
      │
      ▼
[ LAYER 3: AI/ML CORE PIPELINE ]
  - Feature Extraction: RGB/HSV colorimetry + GLCM micro-granularity texture
  - 400–1000 nm Spectral Signature normalization & peak detection
  - Multi-Model Ensemble: XGBoost (70% primary anchor) + RF + SVM + MLP
  - Conformal Prediction: Split conformal confidence intervals (95% coverage)
  - Explainable AI (SHAP): Directional feature attribution & FSO plain-language summary
  - Tier-2 Routing Logic: Flags high-lead samples for confirmatory LA-ICP-MS
      │
      ▼
[ LAYER 4: APPLICATION & TRACEABILITY ]
  - RESTful API (FastAPI backend conforming to Section 7.2 contract)
  - Web Dashboard: Medical-device / fintech-grade dark mode (#080b11 + Turmeric Gold #e8a33d)
  - Radial Spring Gauge with dynamic color interpolation (Red → Amber → Green)
  - Tamper-Evident Ledger: SHA-256 append-only hash chain with live integrity audit
  - Public Traceability: Scannable QR code linking to sanitized certificate page
```

---

## 3. Core API Endpoints (Section 7.2 Contract)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/analyze` | Accepts sample image & metadata; returns classification, calibrated interval, SHAP explanation, tier-2 flag, and QR code. |
| `POST` | `/v1/demo-analyze` | Instant screening using authentic curated lab presets. |
| `GET`  | `/v1/results/{id}` | Retrieves stored test result with complete audit trail and calibration state. |
| `GET`  | `/v1/history` | Paginated audit trail filterable by device, location, date, and status. |
| `POST` | `/v1/devices/{id}/calibrate` | Logs optical calibration event against certified reference tile. |
| `GET`  | `/v1/devices/{id}/drift` | Optical sensor aging and ambient leakage drift status. |
| `POST` | `/v1/traceability/record` | Manually anchors a test result to the cryptographic hash chain. |
| `GET`  | `/v1/traceability/{qr_code}` | Public verification endpoint for consumers and retailers. |
| `GET`  | `/v1/ledger` | Returns all blocks and live cryptographic chain integrity verification. |
| `GET`  | `/v1/compliance/benchmarks` | Returns Codex/FSSAI benchmarks and ISO/IEC 17025 validation metrics. |
| `GET`  | `/v1/devices` | Lists fleet units across mandis and labs. |

---

## 4. Limit of Detection (LOD) & Regulatory Benchmarks

Benchmarked against **Codex Alimentarius CXS 193-1995** and **FSSAI Food Safety and Standards (Contaminants, Toxins and Residues) Regulations** (10 µg/g lead limit):

| Adulterant | TurmericGuard LOD | Target Threshold | Primary Optical / Spectral Mechanism | Confirmatory Standard |
|---|---|---|---|---|
| **Lead Chromate (PbCrO₄)** | **2.1% w/w** | < 3–5% w/w | Reflectance step edge at 530nm + high saturation luminance | **LA-ICP-MS** (Lead Isotope Ratio ²⁰⁸Pb/²⁰⁶Pb vs ²⁰⁷Pb/²⁰⁶Pb) |
| **Metanil Yellow** | **1.8% w/w** | < 3–5% w/w | Anomalous absorption trough at 480nm & red-orange hue shift | Reversed-Phase **HPLC-DAD** |
| **Acid Orange 7** | **2.4% w/w** | < 3–5% w/w | Red spectral dominance (R/G > 1.6) & suppressed hue (< 25°) | Tandem Mass Spec (**LC-MS/MS**) |
| **Inert Fillers (Chalk/Starch)** | **3.5% w/w** | < 5.0% w/w | Desaturation (< 50%) & broad NIR scattering attenuation | **Acid-Insoluble Ash** (AOAC 941.12) |

---

## 5. Quickstart

### Prerequisites
- Python 3.9+
- Pip dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

### Run Server Locally
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 5000 --reload
```
Open your browser at: **`http://127.0.0.1:5000`**

### Run Automated Test Suite
```bash
python -m pytest tests/test_api.py -v
```

---

## 6. Cloud Deployment & Live Backend Integration

To deploy the production Python backend (FastAPI + INT8 MultiTaskCNN + OOD Detector) so that live visitors on GitHub Pages or mobile devices receive real-time neural inferences:

### Option A: Render (Zero-Config 1-Click Deploy)
This repository includes a native `render.yaml` Blueprint.
1. Sign up / Log in to [Render](https://render.com).
2. Connect your GitHub repository: `https://github.com/riishilmmehta/turmericguard-ai`.
3. Render automatically provisions the web service (`uvicorn app:app --host 0.0.0.0 --port $PORT`).
4. Set the deployed URL as `PRODUCTION_BACKEND_URL` in `templates/index.html` (default: `https://turmericguard-ai-backend.onrender.com`).

### Option B: Hugging Face Spaces (Docker Space)
1. Create a new Space on [Hugging Face](https://huggingface.co/new-space) using SDK: `Docker`.
2. Connect or push this repository; Hugging Face uses the included `Dockerfile`.

### Option C: Railway or Fly.io
1. Deploy using the included `Procfile` and `Dockerfile`.

---

## 7. Directory Structure
```
turmericguard-ai/
├── app.py                      # FastAPI server with all Section 7.2 endpoints
├── requirements.txt            # Python dependencies
├── core/
│   ├── vision_pipeline.py      # Dynamic ROI mound extraction, ambient Lux/Kelvin estimator & CIELAB normalizer
│   ├── multitask_cnn.py        # Multi-task CNN (Classification + Huber Loss Regression) & INT8 PTQ engine
│   ├── feature_extraction.py   # RGB, HSV, GLCM texture & 400-1000nm spectral normalizer
│   ├── models_ensemble.py      # XGBoost, RF, SVM, NN & Regressor with joblib caching
│   ├── conformal_predictor.py  # Split conformal confidence intervals & Tier-2 routing
│   ├── explainability.py       # SHAP feature attribution & plain-language generator
│   ├── traceability_ledger.py  # SHA-256 hash-chained append-only ledger & QR generator
│   ├── fleet_manager.py        # Optical calibration state & sensor drift monitor
│   └── dataset_benchmark.py    # Multi-source presets & ISO/IEC 17025 validation tables
├── mobile_app/
│   ├── react_native/           # React Native / Expo Edge Mobile Application (iOS & Android)
│   │   ├── src/components/     # CameraGuideOverlay (alignment box) & VerificationDashboard
│   │   └── src/services/       # QualityPrecheckService & EdgeInferenceService
│   └── flutter/                # Flutter Edge Mobile Application (iOS & Android)
│       └── lib/screens/        # CameraScreen (custom alignment guide) & VerificationDashboard
├── static/
│   ├── models/                 # Quantized INT8 ONNX & PyTorch weight assets
│   ├── css/                    # Tokens, dashboard, and animation stylesheets
│   ├── js/                     # Real-time visualizers & application scripts
│   ├── samples/                # Authentic multi-source reference imagery
│   └── qrcodes/                # Cryptographic verifiable QR assets
├── templates/                  # Web dashboard & public verification templates
└── tests/
    ├── test_api.py             # Section 7.2 API endpoint & ledger audit tests
    └── test_vision_and_edge_ml.py # Dynamic vision, INT8 latency & quality filter tests
```
