"""
TurmericGuard AI — Out-of-Distribution (OOD) & "Is This Turmeric" Detection Gate
Implements:
1. Immediate Stopgap Heuristic Pre-Filter:
   - Evaluates dominant color HSV (hue 10-88 deg, saturation >= 12%), luminance, and yellow chromaticity.
   - Immediately intercepts non-yellow/non-turmeric objects (staplers, leaves, tables, hands, white paper, etc.)
     before running any adulterant classification.
2. Trained Machine Learning OOD Gate:
   - Binary classifier (turmeric vs not-turmeric) trained on genuine turmeric vs diverse negative objects
     (other powders/spices, hands, tables, floors, packaging, fabric, food items, skin, walls).
   - Feature-space anomaly detector (IsolationForest) guarding in-distribution boundaries.
3. Gallery Stricter Handling:
   - Rejects images without a clear, dominant single powder mound (multi-object scenes, screenshots, memes).
"""

import os
import math
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler

OOD_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'ood_model_cache.joblib')


def check_heuristic_turmeric(color_features, cielab=None):
    """
    Tier 1 Immediate Stopgap Heuristic:
    Checks whether colorimetric & photometric properties conform to turmeric powder physical envelope.
    Returns (is_turmeric: bool, reason: str or None).
    """
    if not color_features or not color_features.get('image_valid', False):
        return False, "Invalid image data or corrupted pixels."

    rgb = color_features.get('rgb', {})
    hsv = color_features.get('hsv', {})
    photometrics = color_features.get('photometrics', {})

    r = float(rgb.get('r', 0))
    g = float(rgb.get('g', 0))
    b = float(rgb.get('b', 0))
    rg_ratio = float(rgb.get('rg_ratio', r / max(1.0, g)))
    rb_ratio = float(rgb.get('rb_ratio', r / max(1.0, b)))
    gb_ratio = float(rgb.get('gb_ratio', g / max(1.0, b)))

    hue = float(hsv.get('h', 0))
    sat = float(hsv.get('s', 0))
    val = float(hsv.get('v', 0))
    brightness = float(photometrics.get('brightness', 0.299 * r + 0.587 * g + 0.114 * b))

    # Calculate approximate CIELAB yellow and red chromaticity
    if cielab:
        b_star = float(cielab.get('b_star', 0))
        a_star = float(cielab.get('a_star', 0))
    else:
        b_star = (r * 0.5 + g * 0.5 - b) * 0.45
        a_star = (r - g) * 0.45

    # 1. Turmeric must have positive yellow chromaticity (b* >= 8.0)
    # Rejects blue, purple, cyan, gray, black, and white objects immediately
    if b_star < 8.0:
        return False, f"Lacks characteristic turmeric yellow chromaticity (b*={b_star:.1f} < 8.0)."

    # 2. Must not be green (a* cannot be strongly negative)
    # Green foliage/matcha/leaves have a* < -4.0
    if a_star < -3.5:
        return False, f"Green hue detected (a*={a_star:.1f} < -3.5) — turmeric must exhibit warm golden undertone."

    # 3. Must have red and green channel dominance over blue
    # Blue objects, purple fabrics, and cool LED specular highlights have b > r * 0.90
    if b > r * 0.92 or b > g * 0.98:
        return False, "Blue channel dominance detected (non-yellow object)."

    # 4. Hue range: 10.0 deg to 88.0 deg
    # Covers the entire spectrum from deep reddish azo dye adulteration (12-25 deg)
    # to natural Indian curcuma (36-46 deg) to industrial lead chromate (48-84 deg).
    # Rejects cyans, blues, magentas, purples, and deep greens.
    if hue < 10.0 or hue > 88.0:
        return False, f"Color hue ({hue:.1f}°) lies outside turmeric physical band (10°–88°)."

    # 5. Saturation threshold: >= 12.0%
    # Rejects achromatic objects: white copy paper, gray tabletops, black floors, silver metal
    if sat < 12.0:
        return False, f"Object is desaturated (saturation {sat:.1f}% < 12.0%) — authentic turmeric exhibits vibrant chroma."

    # 6. Minimum red-to-blue ratio
    if rb_ratio < 1.15:
        return False, f"Low Red/Blue ratio ({rb_ratio:.2f} < 1.15) — insufficient warm spectral reflection."

    # 7. Absolute photometric luminance bounds (must not be completely black or completely blown out)
    if brightness < 20.0:
        return False, "Frame is too dark or underexposed to resolve turmeric pigments."
    if brightness > 250.0 and sat < 15.0:
        return False, "Frame is washed out white with zero pigment density."

    return True, None


class TurmericOODClassifier:
    """
    Tier 2 Trained Machine Learning Out-Of-Distribution Gate.
    Combines:
    1. Heuristic physical color pre-filter (fast rejection)
    2. Trained Binary Classifier (Turmeric vs Diverse Not-Turmeric)
    3. Feature-Space Anomaly Detector (Isolation Forest on genuine turmeric distribution)
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.binary_classifier = None
        self.anomaly_detector = None
        self.is_trained = False
        self._load_or_train()

    def _init_models(self):
        self.binary_classifier = RandomForestClassifier(n_estimators=60, max_depth=6, random_state=42)
        self.anomaly_detector = IsolationForest(contamination=0.01, random_state=42)

    def _generate_ood_training_data(self):
        """
        Generates grounded training dataset of genuine/adulterated turmeric (Positive class)
        alongside a diverse corpus of non-turmeric negative examples:
        - Blue/cyan objects (pens, staplers, jeans, blue plastics)
        - Green foliage/vegetables (leaves, matcha, cucumber, green fabrics)
        - Red objects (chili powder, paprika, red apples, red packaging)
        - Achromatic surfaces (white copy paper, gray granite, white sugar, salt, flour)
        - Dark surfaces (black countertops, dark wood tables, floors, shadows)
        - Skin tones & hands (fingers holding samples)
        - Purple, magenta, pink, and orange synthetic items
        """
        from core.models_ensemble import ensemble_model

        # 1. Grounded positive turmeric corpus
        X_ground, _, _ = ensemble_model._generate_grounded_training_corpus(n_samples_per_class=120)
        pos_X = []
        for vec in X_ground:
            r, g, b = float(vec[0]), float(vec[1]), float(vec[2])
            rg_r, rb_r, gb_r = float(vec[6]), float(vec[7]), float(vec[8])
            h, s, v = float(vec[9]), float(vec[10]), float(vec[11])
            bright = float(vec[14])
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            pos_X.append([r, g, b, rg_r, rb_r, gb_r, h, s, v, bright, a_star, b_star])

        # 2. Negative Class: Diverse Non-Turmeric Objects
        neg_X = []
        np.random.seed(42)

        # Category A: Blue / Cyan objects (stapler, sky, ocean, blue fabric, pens)
        for _ in range(120):
            r = np.random.uniform(10.0, 70.0)
            g = np.random.uniform(50.0, 150.0)
            b = np.random.uniform(150.0, 245.0)
            h = np.random.uniform(185.0, 250.0)
            s = np.random.uniform(55.0, 95.0)
            v = np.random.uniform(50.0, 95.0)
            bright = 0.299 * r + 0.587 * g + 0.114 * b
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            neg_X.append([r, g, b, r / max(1.0, g), r / max(1.0, b), g / max(1.0, b), h, s, v, bright, a_star, b_star])

        # Category B: Green foliage / vegetables / matcha / cucumber / grass
        for _ in range(120):
            r = np.random.uniform(20.0, 80.0)
            g = np.random.uniform(110.0, 200.0)
            b = np.random.uniform(30.0, 90.0)
            h = np.random.uniform(95.0, 160.0)
            s = np.random.uniform(55.0, 90.0)
            v = np.random.uniform(45.0, 80.0)
            bright = 0.299 * r + 0.587 * g + 0.114 * b
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            neg_X.append([r, g, b, r / max(1.0, g), r / max(1.0, b), g / max(1.0, b), h, s, v, bright, a_star, b_star])

        # Category C: Red / Deep Orange-Red (chili powder, paprika, red apples, red cloth)
        for _ in range(120):
            r = np.random.uniform(180.0, 245.0)
            g = np.random.uniform(15.0, 60.0)
            b = np.random.uniform(15.0, 50.0)
            h = np.random.uniform(0.0, 8.5)
            s = np.random.uniform(75.0, 98.0)
            v = np.random.uniform(60.0, 95.0)
            bright = 0.299 * r + 0.587 * g + 0.114 * b
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            neg_X.append([r, g, b, r / max(1.0, g), r / max(1.0, b), g / max(1.0, b), h, s, v, bright, a_star, b_star])

        # Category D: Achromatic surfaces (white copy paper, white sugar, salt, flour, gray desks, marble)
        for _ in range(150):
            bg = np.random.uniform(15.0, 240.0)
            r = bg + np.random.normal(0, 2)
            g = bg + np.random.normal(0, 2)
            b = bg + np.random.normal(0, 2)
            h = np.random.uniform(0.0, 360.0)
            s = np.random.uniform(0.0, 7.0)
            v = np.random.uniform(10.0, 98.0)
            bright = bg
            neg_X.append([r, g, b, 1.0, 1.0, 1.0, h, s, v, bright, 0.0, 0.0])

        # Category E: Dark surfaces (black laptops, shadows, dark wood, floorboards)
        for _ in range(100):
            r = np.random.uniform(10.0, 45.0)
            g = np.random.uniform(10.0, 40.0)
            b = np.random.uniform(8.0, 35.0)
            h = np.random.uniform(20.0, 45.0)
            s = np.random.uniform(15.0, 35.0)
            v = np.random.uniform(5.0, 18.0)
            bright = 0.299 * r + 0.587 * g + 0.114 * b
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            neg_X.append([r, g, b, r / max(1.0, g), r / max(1.0, b), g / max(1.0, b), h, s, v, bright, a_star, b_star])

        # Category F: Human skin tones & hands
        for _ in range(120):
            r = np.random.uniform(180.0, 235.0)
            g = np.random.uniform(130.0, 185.0)
            b = np.random.uniform(110.0, 165.0)
            h = np.random.uniform(14.0, 24.0)
            s = np.random.uniform(25.0, 42.0)
            v = np.random.uniform(65.0, 90.0)
            bright = 0.299 * r + 0.587 * g + 0.114 * b
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            neg_X.append([r, g, b, r / max(1.0, g), r / max(1.0, b), g / max(1.0, b), h, s, v, bright, a_star, b_star])

        # Category G: Purple, magenta, pink, violet items
        for _ in range(100):
            r = np.random.uniform(140.0, 220.0)
            g = np.random.uniform(20.0, 80.0)
            b = np.random.uniform(130.0, 210.0)
            h = np.random.uniform(280.0, 335.0)
            s = np.random.uniform(50.0, 85.0)
            v = np.random.uniform(50.0, 85.0)
            bright = 0.299 * r + 0.587 * g + 0.114 * b
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45
            neg_X.append([r, g, b, r / max(1.0, g), r / max(1.0, b), g / max(1.0, b), h, s, v, bright, a_star, b_star])

        X = np.array(pos_X + neg_X, dtype=np.float32)
        y = np.array([1] * len(pos_X) + [0] * len(neg_X), dtype=np.int32)
        return X, y

    def _load_or_train(self):
        if os.path.exists(OOD_CACHE_FILE):
            try:
                bundle = joblib.load(OOD_CACHE_FILE)
                self.scaler = bundle['scaler']
                self.binary_classifier = bundle['binary_classifier']
                self.anomaly_detector = bundle['anomaly_detector']
                self.is_trained = True
                return
            except Exception:
                pass

        self._init_models()
        self._train_and_cache()

    def _train_and_cache(self):
        X, y = self._generate_ood_training_data()
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.binary_classifier.fit(X_scaled, y)

        # Anomaly detector fitted exclusively on positive (turmeric) class
        X_pos = X_scaled[y == 1]
        self.anomaly_detector.fit(X_pos)

        self.is_trained = True

        bundle = {
            'scaler': self.scaler,
            'binary_classifier': self.binary_classifier,
            'anomaly_detector': self.anomaly_detector
        }
        try:
            joblib.dump(bundle, OOD_CACHE_FILE)
        except Exception:
            pass

    def _extract_12d_vector(self, color_features, cielab=None):
        rgb = color_features.get('rgb', {})
        hsv = color_features.get('hsv', {})
        photometrics = color_features.get('photometrics', {})

        r = float(rgb.get('r', 180.0))
        g = float(rgb.get('g', 150.0))
        b = float(rgb.get('b', 60.0))
        rg_ratio = float(rgb.get('rg_ratio', r / max(1.0, g)))
        rb_ratio = float(rgb.get('rb_ratio', r / max(1.0, b)))
        gb_ratio = float(rgb.get('gb_ratio', g / max(1.0, b)))

        h = float(hsv.get('h', 42.0))
        s = float(hsv.get('s', 70.0))
        v = float(hsv.get('v', 75.0))
        bright = float(photometrics.get('brightness', 0.299 * r + 0.587 * g + 0.114 * b))

        if cielab:
            b_star = float(cielab.get('b_star', (r * 0.5 + g * 0.5 - b) * 0.45))
            a_star = float(cielab.get('a_star', (r - g) * 0.45))
        else:
            b_star = (r * 0.5 + g * 0.5 - b) * 0.45
            a_star = (r - g) * 0.45

        return [r, g, b, rg_ratio, rb_ratio, gb_ratio, h, s, v, bright, a_star, b_star]

    def evaluate(self, color_features, cielab=None, precomputed_vision=None, capture_source="live_camera"):
        """
        Executes complete Out-of-Distribution (OOD) verification gate:
        1. Evaluates Tier-1 physical colorimetric heuristic (HSV bounds + CIELAB b* yellow chromaticity).
        2. Evaluates Tier-2 trained binary classifier (P(turmeric)).
        3. Evaluates feature-space anomaly detector (in-distribution vs outlier).
        4. If gallery import: enforces that a distinct, clear single powder mound was detected
           (rejects multi-object photos, screenshots, memes, and landscape views).

        Returns:
          dict with:
            'is_turmeric': bool
            'rejection_code': str or None
            'rejection_message': "This doesn't look like turmeric powder. Please scan a turmeric sample."
            'supporting_text': "Make sure the sample fills the guide box and is turmeric powder."
            'ood_score': float (0.0 - 1.0)
            'capture_source': "live_camera" | "gallery_import"
        """
        # Step 0: Gallery Import Stricter Mound Presence Check
        if capture_source == "gallery_import" and precomputed_vision:
            roi = precomputed_vision.get('roi', {})
            detected = roi.get('detected_mound', False)
            coverage = roi.get('contour_meta', {}).get('foreground_coverage_pct', 0.0)
            # If no clear single mound found or coverage < 5% (e.g. meme, screenshot, wide room)
            if not detected or coverage < 5.0:
                return {
                    'is_turmeric': False,
                    'rejection_code': 'NO_DOMINANT_SAMPLE_MOUND',
                    'rejection_message': "This doesn't look like turmeric powder. Please scan a turmeric sample.",
                    'supporting_text': "Make sure the sample fills the guide box and is turmeric powder.",
                    'ood_score': 0.0,
                    'capture_source': capture_source,
                    'details': "Gallery photo does not contain a single clear, dominant powder mound."
                }

        # Step 1: Immediate Heuristic Pre-Filter
        h_ok, h_reason = check_heuristic_turmeric(color_features, cielab=cielab)
        if not h_ok:
            return {
                'is_turmeric': False,
                'rejection_code': 'HEURISTIC_COLOR_OOD',
                'rejection_message': "This doesn't look like turmeric powder. Please scan a turmeric sample.",
                'supporting_text': "Make sure the sample fills the guide box and is turmeric powder.",
                'ood_score': 0.02,
                'capture_source': capture_source,
                'details': h_reason
            }

        # Step 2: Binary Classifier & Anomaly Detector
        vec = self._extract_12d_vector(color_features, cielab=cielab)
        vec_scaled = self.scaler.transform([vec])

        # P(turmeric)
        p_turmeric = float(self.binary_classifier.predict_proba(vec_scaled)[0, 1])

        # Anomaly score (1 = inlier, -1 = outlier)
        anomaly_pred = int(self.anomaly_detector.predict(vec_scaled)[0])

        # A sample is accepted if the trained binary classifier is confident it is turmeric powder
        # (and does not trigger anomaly rejection in the borderline band)
        is_accepted = (p_turmeric >= 0.65) if p_turmeric >= 0.85 else (p_turmeric >= 0.65 and anomaly_pred == 1)

        if not is_accepted:
            reason = (
                f"Trained OOD detector classified as non-turmeric (P(turmeric)={p_turmeric:.2f}, "
                f"Anomaly={'Outlier' if anomaly_pred == -1 else 'Inlier'})."
            )
            return {
                'is_turmeric': False,
                'rejection_code': 'MODEL_OOD_REJECTION',
                'rejection_message': "This doesn't look like turmeric powder. Please scan a turmeric sample.",
                'supporting_text': "Make sure the sample fills the guide box and is turmeric powder.",
                'ood_score': round(p_turmeric, 3),
                'capture_source': capture_source,
                'details': reason
            }

        return {
            'is_turmeric': True,
            'rejection_code': None,
            'rejection_message': None,
            'supporting_text': None,
            'ood_score': round(p_turmeric, 3),
            'capture_source': capture_source,
            'details': "Sample confirmed within turmeric physical and spectral distribution."
        }


# Singleton instance
ood_detector = TurmericOODClassifier()
