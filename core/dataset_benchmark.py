"""
TurmericGuard AI — Curated Reference Presets
Implements Section 3, 6.6, and 10 of the Technical Specification:
- Multi-source spice dataset presets (Alleppey, Lakadong, Erode, Sangli)
- Benchmarked limits of detection (LOD) vs Codex Alimentarius & FSSAI
- Curated reference calibration samples for client previews and automated triage
"""

# Standardized Curated Demo Presets (for zero-latency instant analysis and demonstration)
CURATED_DEMO_PRESETS = {
    "pure_alleppey": {
        "title": "Authentic Alleppey Pure Turmeric (Lot: #ATP-6701)",
        "variety": "Alleppey Supreme Grade",
        "origin": "Kuttanad, Alleppey, Kerala",
        "sample_type": "pure",
        "description": "Certified pure geographical indication turmeric powder with 5.8% natural curcumin content. Natural earthy aroma, rich golden ochre color.",
        "image_file": "pure_alleppey.jpg",
        "expected_status": "PURE",
        "features": {
            "rgb": {"r": 199.5, "g": 165.2, "b": 55.3, "r_std": 11.2, "g_std": 9.8, "b_std": 8.1, "rg_ratio": 1.21, "rb_ratio": 3.61, "gb_ratio": 2.99},
            "hsv": {"h": 43.2, "s": 72.5, "v": 78.3, "h_std": 2.4, "s_std": 3.8},
            "photometrics": {"brightness": 156.4, "uniformity": 83.5},
            "texture_glcm": {"contrast": 13.8, "homogeneity": 87.2, "energy": 44.1}
        }
    },
    "lead_chromate_8pct": {
        "title": "Adulterated Sample: 8% Lead Chromate (Lot: #LC-Pb-418)",
        "variety": "Polished Commercial Grade",
        "origin": "Unregulated Market Mandi, North India",
        "sample_type": "lead_chromate",
        "description": "Commercial turmeric powder heavily laced with toxic industrial pigment Lead Chromate (PbCrO4) to mask dull color. Exceeds FSSAI lead limit by >120x.",
        "image_file": "lead_chromate_8pct.jpg",
        "expected_status": "ADULTERATED",
        "features": {
            "rgb": {"r": 236.4, "g": 212.8, "b": 38.5, "r_std": 7.4, "g_std": 6.8, "b_std": 4.9, "rg_ratio": 1.11, "rb_ratio": 6.14, "gb_ratio": 5.53},
            "hsv": {"h": 52.8, "s": 83.7, "v": 92.7, "h_std": 1.8, "s_std": 2.9},
            "photometrics": {"brightness": 210.2, "uniformity": 89.2},
            "texture_glcm": {"contrast": 9.2, "homogeneity": 91.5, "energy": 58.4}
        }
    },
    "metanil_yellow_5pct": {
        "title": "Adulterated Sample: 5% Metanil Yellow (Lot: #MY-DYE-920)",
        "variety": "Blended Curry Powder Stock",
        "origin": "Wholesale Bazaar, Maharashtra",
        "sample_type": "metanil_yellow",
        "description": "Turmeric adulterated with synthetic Metanil Yellow azo dye. Shows distinct artificial red-orange tint and anomalous 480nm absorption trough.",
        "image_file": "metanil_yellow_5pct.jpg",
        "expected_status": "ADULTERATED",
        "features": {
            "rgb": {"r": 224.2, "g": 148.6, "b": 44.1, "r_std": 16.5, "g_std": 14.1, "b_std": 12.0, "rg_ratio": 1.51, "rb_ratio": 5.08, "gb_ratio": 3.37},
            "hsv": {"h": 32.4, "s": 80.3, "v": 87.9, "h_std": 3.1, "s_std": 4.2},
            "photometrics": {"brightness": 162.8, "uniformity": 68.4},
            "texture_glcm": {"contrast": 16.8, "homogeneity": 81.4, "energy": 46.2}
        }
    },
    "chalk_filler_15pct": {
        "title": "Adulterated Sample: 15% Inert Chalk / Starch (Lot: #FL-CHK-021)",
        "variety": "Loose Bulk Powder",
        "origin": "Local Unbranded Spice Market",
        "sample_type": "chalk_filler",
        "description": "Turmeric diluted with chalk, starch, and soapstone powder. Demonstrates severe color bleaching, depleted curcuminoid absorption, and powdery white clumping.",
        "image_file": "chalk_filler_15pct.jpg",
        "expected_status": "ADULTERATED",
        "features": {
            "rgb": {"r": 218.0, "g": 204.5, "b": 142.0, "r_std": 21.2, "g_std": 18.9, "b_std": 19.5, "rg_ratio": 1.07, "rb_ratio": 1.54, "gb_ratio": 1.44},
            "hsv": {"h": 46.5, "s": 34.8, "v": 85.5, "h_std": 4.5, "s_std": 6.8},
            "photometrics": {"brightness": 198.5, "uniformity": 52.1},
            "texture_glcm": {"contrast": 26.5, "homogeneity": 72.8, "energy": 33.2}
        }
    },
    "borderline_suspicious": {
        "title": "Suspicious Borderline Sample: 1.8% Low-Dye (Lot: #SUSP-991)",
        "variety": "Farm Gate Aggregate",
        "origin": "Regional Mandi Aggregator",
        "sample_type": "suspicious",
        "description": "Borderline quality turmeric showing subtle spectral distortion near detection limit (1.8% w/w). Requires mandatory Tier-2 laboratory confirmatory testing.",
        "image_file": "pure_alleppey.jpg",
        "expected_status": "SUSPICIOUS",
        "features": {
            "rgb": {"r": 208.5, "g": 168.2, "b": 51.0, "r_std": 14.5, "g_std": 12.1, "b_std": 10.5, "rg_ratio": 1.24, "rb_ratio": 4.08, "gb_ratio": 3.30},
            "hsv": {"h": 37.8, "s": 75.5, "v": 81.8, "h_std": 3.0, "s_std": 4.5},
            "photometrics": {"brightness": 169.2, "uniformity": 72.5},
            "texture_glcm": {"contrast": 15.2, "homogeneity": 84.1, "energy": 42.8}
        }
    },
    "non_turmeric_object": {
        "title": "Non-Turmeric Object (Negative Sample: Blue Packaging / Desk)",
        "variety": "Out-of-Distribution Control",
        "origin": "Laboratory Negative Benchmark",
        "sample_type": "non_turmeric",
        "description": "Out-of-distribution sample (blue background / non-spice material). Demonstrates immediate rejection by the OOD gate with zero adulteration classification or confidence hallucination.",
        "image_file": "non_turmeric_sample.jpg",
        "expected_status": "REJECTED",
        "features": {
            "rgb": {"r": 35.0, "g": 95.0, "b": 180.0, "r_std": 15.0, "g_std": 12.0, "b_std": 18.0, "rg_ratio": 0.37, "rb_ratio": 0.19, "gb_ratio": 0.53},
            "hsv": {"h": 215.0, "s": 80.5, "v": 70.6, "h_std": 5.0, "s_std": 6.0},
            "photometrics": {"brightness": 95.0, "uniformity": 40.0},
            "texture_glcm": {"contrast": 35.0, "homogeneity": 60.0, "energy": 25.0}
        }
    }
}
