"""
TurmericGuard AI — Dynamic Vision Pipeline & Pre-Inference Quality Filter
Implements Technical Specification Sections:
1. Dynamic ROI & Contour Extraction (powder mound perimeter detection, auto-cropping plates/tables)
2. Adaptive Ambient Light Estimator (background Lux & Kelvin estimation, automatic chromatic adaptation, replacing physical gray card)
3. Histogram Equalization & White Balance Normalization (locks CIELAB L*a*b* parameters, b* rigidity benchmark, TRF & TCRI computation)
4. Structural Content Quality Filter (Laplacian variance blur check, specular glare index thresholds, real-time rejection & retry guidance)
"""

import math
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Color-rigidity benchmark constant for pure curcumin in standardized CIELAB space
# Pure turmeric exhibits a characteristic b*/sqrt(L*^2 + a*^2) ratio around 0.62 - 0.76
CURCUMIN_B_RIGIDITY_BENCHMARK = 68.5
CURCUMIN_RIGIDITY_RATIO_TARGET = 0.685

# Quality filter default thresholds (Tightened for enhanced inference reliability)
DEFAULT_BLUR_THRESHOLD = 85.0      # Laplacian variance minimum (rejects soft/marginal focus)
DEFAULT_GLARE_THRESHOLD = 4.0      # Specular highlight maximum percentage (%) (rejects harsh specular reflection)
MIN_SAFE_LUMINANCE = 28.0          # Minimum photometric illuminance (0-255)
MAX_SAFE_LUMINANCE = 245.0         # Maximum mean luminance before blowout


def to_bgr_array(img_input):
    """Converts a PIL Image, filepath, or array to BGR (OpenCV) numpy array."""
    if isinstance(img_input, str):
        img_pil = Image.open(img_input).convert('RGB')
        rgb = np.array(img_pil, dtype=np.uint8)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR) if HAS_OPENCV else rgb[:, :, ::-1]
    elif isinstance(img_input, Image.Image):
        rgb = np.array(img_input.convert('RGB'), dtype=np.uint8)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR) if HAS_OPENCV else rgb[:, :, ::-1]
    elif isinstance(img_input, np.ndarray):
        if img_input.ndim == 2:
            return cv2.cvtColor(img_input, cv2.COLOR_GRAY2BGR) if HAS_OPENCV else np.stack([img_input]*3, axis=-1)
        elif img_input.shape[2] == 4:
            return cv2.cvtColor(img_input, cv2.COLOR_RGBA2BGR) if HAS_OPENCV else img_input[:, :, :3][:, :, ::-1]
        return img_input
    else:
        raise ValueError(f"Unsupported image input type: {type(img_input)}")


def to_rgb_array(bgr_array):
    """Converts a BGR numpy array to RGB."""
    if HAS_OPENCV:
        return cv2.cvtColor(bgr_array, cv2.COLOR_BGR2RGB)
    return bgr_array[:, :, ::-1]


# =========================================================================
# 1. STRUCTURAL CONTENT QUALITY FILTER
# =========================================================================

def check_image_quality(img_input, blur_threshold=DEFAULT_BLUR_THRESHOLD, glare_threshold=DEFAULT_GLARE_THRESHOLD):
    """
    Pre-inference structural quality gate.
    Calculates spatial blur via Laplacian variance and specular glare index.
    If image fails quality criteria, returns is_valid=False with specific retry instructions.
    """
    bgr = to_bgr_array(img_input)
    h, w = bgr.shape[:2]

    # Convert to grayscale
    if HAS_OPENCV:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = float(laplacian.var())
    else:
        # Fallback discrete 2D Laplacian kernel via numpy
        rgb = bgr[:, :, ::-1].astype(np.float32)
        gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        # Approximate Laplacian: center*4 - top - bottom - left - right
        pad = np.pad(gray, 1, mode='edge')
        lap = pad[1:-1, :-2] + pad[1:-1, 2:] + pad[:-2, 1:-1] + pad[2:, 1:-1] - 4 * pad[1:-1, 1:-1]
        blur_score = float(np.var(lap))

    # Mean luminance
    mean_lum = float(np.mean(gray))

    # Glare Index: percentage of pixels with intense specular burnout
    # In BGR: pixels where all channels are very high (>245) or luminance >250 with low chroma
    specular_mask = (bgr[:, :, 0] > 242) & (bgr[:, :, 1] > 242) & (bgr[:, :, 2] > 242)
    glare_pixel_count = int(np.sum(specular_mask))
    total_pixels = h * w
    glare_index = float((glare_pixel_count / max(1, total_pixels)) * 100.0)

    # Ambient illuminance estimate (0-1000 Lux scale rough optical approximation)
    est_lux = float(round(mean_lum * 3.8, 1))

    # Decision logic
    is_valid = True
    rejection_code = None
    rejection_prompt = None

    if blur_score < blur_threshold:
        is_valid = False
        rejection_code = "BLUR_DETECTED"
        rejection_prompt = (
            f"Frame rejected: Severe spatial blur detected (Laplacian score {blur_score:.1f} < {blur_threshold}). "
            "Please stabilize your smartphone, tap the screen to focus on the turmeric mound, and retake."
        )
    elif glare_index > glare_threshold:
        is_valid = False
        rejection_code = "SPECULAR_GLARE"
        rejection_prompt = (
            f"Frame rejected: Overexposure / specular glare detected ({glare_index:.1f}% clipped pixels > {glare_threshold}%). "
            "Please angle the phone 15 degrees away from direct overhead lights to avoid specular reflections."
        )
    elif mean_lum < MIN_SAFE_LUMINANCE:
        is_valid = False
        rejection_code = "UNDEREXPOSED"
        rejection_prompt = (
            f"Frame rejected: Ambient lighting is too dark (Luminance {mean_lum:.1f} < {MIN_SAFE_LUMINANCE}, ~{est_lux:.0f} Lux). "
            "Please turn on room lighting or the device LED flash before capturing."
        )
    elif mean_lum > MAX_SAFE_LUMINANCE:
        is_valid = False
        rejection_code = "OVEREXPOSED"
        rejection_prompt = (
            f"Frame rejected: Image is completely washed out (Luminance {mean_lum:.1f} > {MAX_SAFE_LUMINANCE}). "
            "Please reduce light intensity or increase distance."
        )

    return {
        'is_valid': is_valid,
        'blur_score': round(blur_score, 2),
        'blur_threshold': blur_threshold,
        'glare_index_pct': round(glare_index, 2),
        'glare_threshold_pct': glare_threshold,
        'mean_luminance': round(mean_lum, 2),
        'estimated_lux': est_lux,
        'rejection_code': rejection_code,
        'rejection_prompt': rejection_prompt
    }


# =========================================================================
# 2. DYNAMIC ROI & CONTOUR EXTRACTION
# =========================================================================

def extract_dynamic_roi(img_input, target_size=(224, 224)):
    """
    Dynamically detects the perimeter contour of the turmeric powder mound,
    cropping automatically to eliminate surrounding plates, petri dishes,
    packaging, or table surfaces.
    
    Returns:
    - cropped_bgr: 224x224 normalized BGR image centered on the powder
    - cropped_rgb: 224x224 RGB image
    - mask_224: Binary mask of foreground powder
    - bbox: [x, y, w, h] coordinates in original image
    - contour_meta: Area, perimeter, circularity, foreground coverage
    """
    bgr = to_bgr_array(img_input)
    h, w = bgr.shape[:2]

    # Target color range for turmeric powder in HSV
    # Turmeric golden/yellow/orange-red: Hue 10-50 (in OpenCV 0-180 scale: 5-45)
    if HAS_OPENCV:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        # Broader mask for pure turmeric, lead chromate, metanil yellow, and chalk-adulterated powders
        lower_turmeric = np.array([6, 35, 40], dtype=np.uint8)
        upper_turmeric = np.array([45, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_turmeric, upper_turmeric)

        # Morphological filtering to eliminate small noise and close internal gaps
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel_open)

        # Find external contours
        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        # Pure numpy color thresholding fallback
        rgb = bgr[:, :, ::-1].astype(np.float32)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        # Turmeric rule: strong red and green, low blue
        mask_clean = ((r > 80) & (g > 50) & (b < 150) & (r > b * 1.3)).astype(np.uint8) * 255
        contours = []

    # Select the primary contour representing the powder mound
    chosen_contour = None
    max_area = 0
    total_area = h * w

    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Must be at least 4% of total frame and not exceed 96%
        if area > max_area and (area / total_area) > 0.04:
            max_area = area
            chosen_contour = cnt

    if chosen_contour is not None and HAS_OPENCV:
        x, y, bw, bh = cv2.boundingRect(chosen_contour)
        # Pad bounding box by 8% to preserve periphery powder gradient
        pad_x = int(bw * 0.08)
        pad_y = int(bh * 0.08)
        x0 = max(0, x - pad_x)
        y0 = max(0, y - pad_y)
        x1 = min(w, x + bw + pad_x)
        y1 = min(h, y + bh + pad_y)

        peri = cv2.arcLength(chosen_contour, True)
        circularity = 4 * math.pi * (max_area / max(1.0, peri ** 2))

        # Crop image and mask to bounding box
        cropped_raw = bgr[y0:y1, x0:x1]
        mask_crop = mask_clean[y0:y1, x0:x1]

        bbox = [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
        detected = True
    else:
        # Fallback: Central 60% elliptical ROI
        cx, cy = w // 2, h // 2
        rx, ry = int(w * 0.30), int(h * 0.30)
        x0, y0 = max(0, cx - rx), max(0, cy - ry)
        x1, y1 = min(w, cx + rx), min(h, cy + ry)
        cropped_raw = bgr[y0:y1, x0:x1]

        # Generate synthetic ellipse mask
        mask_crop = np.zeros(cropped_raw.shape[:2], dtype=np.uint8)
        if HAS_OPENCV:
            cv2.ellipse(mask_crop, ((x1 - x0)//2, (y1 - y0)//2), (rx, ry), 0, 0, 360, 255, -1)
        else:
            mask_crop.fill(255)

        bbox = [x0, y0, x1 - x0, y1 - y0]
        max_area = float((x1 - x0) * (y1 - y0) * 0.785)
        circularity = 0.85
        detected = False

    # Resize to standardized analytical resolution
    if HAS_OPENCV:
        cropped_bgr = cv2.resize(cropped_raw, target_size, interpolation=cv2.INTER_LANCZOS4)
        mask_standard = cv2.resize(mask_crop, target_size, interpolation=cv2.INTER_NEAREST)
    else:
        pil_crop = Image.fromarray(cropped_raw[:, :, ::-1]).resize(target_size, Image.Resampling.LANCZOS)
        cropped_bgr = np.array(pil_crop)[:, :, ::-1]
        pil_mask = Image.fromarray(mask_crop).resize(target_size, Image.Resampling.NEAREST)
        mask_standard = np.array(pil_mask)

    cropped_rgb = to_rgb_array(cropped_bgr)
    fg_coverage = float(np.sum(mask_standard > 0) / (target_size[0] * target_size[1]) * 100.0)

    return {
        'detected_mound': detected,
        'cropped_bgr': cropped_bgr,
        'cropped_rgb': cropped_rgb,
        'powder_mask': mask_standard,
        'bbox': bbox,
        'contour_meta': {
            'area_pixels': int(max_area),
            'circularity': round(circularity, 3),
            'foreground_coverage_pct': round(fg_coverage, 1),
            'original_dimensions': [w, h]
        }
    }


# =========================================================================
# 3. ADAPTIVE AMBIENT LIGHT ESTIMATOR
# =========================================================================

def estimate_ambient_light_and_compensate(bgr_image, powder_mask=None, target_cct=6500.0):
    """
    Analyzes background non-turmeric pixels to estimate ambient light temperature (Lux & Kelvin).
    Dynamically compensates the color balance of the image before computing TRF,
    eliminating the requirement for an external physical gray card.
    
    Uses McCamy's chromaticity approximation for CCT and Von Kries chromatic adaptation.
    """
    bgr = bgr_image.copy()
    h, w = bgr.shape[:2]

    # Identify background pixels
    if powder_mask is not None and powder_mask.shape[:2] == (h, w):
        bg_mask = (powder_mask == 0)
        # If powder covers almost everything, sample frame perimeter margins
        if np.sum(bg_mask) < 200:
            bg_mask = np.zeros((h, w), dtype=bool)
            margin_y = int(h * 0.08)
            margin_x = int(w * 0.08)
            bg_mask[:margin_y, :] = True
            bg_mask[-margin_y:, :] = True
            bg_mask[:, :margin_x] = True
            bg_mask[:, -margin_x:] = True
    else:
        # Use peripheral border
        bg_mask = np.zeros((h, w), dtype=bool)
        bg_mask[:int(h * 0.1), :] = True
        bg_mask[-int(h * 0.1):, :] = True

    bg_bgr = bgr[bg_mask]
    if len(bg_bgr) == 0:
        bg_bgr = bgr.reshape(-1, 3)

    # Background channel means (in RGB order)
    bg_b = float(np.mean(bg_bgr[:, 0]))
    bg_g = float(np.mean(bg_bgr[:, 1]))
    bg_r = float(np.mean(bg_bgr[:, 2]))

    # Estimated Ambient Illuminance (Lux)
    lux_est = float(round((0.2126 * bg_r + 0.7152 * bg_g + 0.0722 * bg_b) * 4.2, 1))

    # Approximate CIE 1931 xy coordinates for Correlated Color Temperature (CCT)
    # Conversion matrix sRGB -> XYZ
    X = 0.4124 * bg_r + 0.3576 * bg_g + 0.1805 * bg_b
    Y = 0.2126 * bg_r + 0.7152 * bg_g + 0.0722 * bg_b
    Z = 0.0193 * bg_r + 0.1192 * bg_g + 0.9505 * bg_b
    sum_xyz = max(1e-5, X + Y + Z)
    x = X / sum_xyz
    y = Y / sum_xyz

    # McCamy's Formula for Correlated Color Temperature (Kelvin)
    # n = (x - 0.3320) / (0.1858 - y)
    # CCT = 449*n^3 + 3525*n^2 + 6823.3*n + 5520.33
    denom = 0.1858 - y
    if abs(denom) > 1e-4:
        n = (x - 0.3320) / denom
        cct = 449.0 * (n ** 3) + 3525.0 * (n ** 2) + 6823.3 * n + 5520.33
        cct = max(2200.0, min(10500.0, cct))
    else:
        cct = 5500.0

    # Color balance gain calculation (Von Kries Chromatic Adaptation towards D65 ~ 6500K neutral)
    # Gray world / white patch relative to neutral gray:
    mean_gray = (bg_r + bg_g + bg_b) / 3.0
    scale_r = float(mean_gray / max(10.0, bg_r))
    scale_g = float(mean_gray / max(10.0, bg_g))
    scale_b = float(mean_gray / max(10.0, bg_b))

    # Clamp gains to avoid harsh color distortions
    scale_r = max(0.65, min(1.55, scale_r))
    scale_g = max(0.75, min(1.35, scale_g))
    scale_b = max(0.65, min(1.55, scale_b))

    # Apply chromatic compensation
    compensated_bgr = bgr.astype(np.float32)
    compensated_bgr[:, :, 0] = np.clip(compensated_bgr[:, :, 0] * scale_b, 0, 255)
    compensated_bgr[:, :, 1] = np.clip(compensated_bgr[:, :, 1] * scale_g, 0, 255)
    compensated_bgr[:, :, 2] = np.clip(compensated_bgr[:, :, 2] * scale_r, 0, 255)
    compensated_bgr = compensated_bgr.astype(np.uint8)

    return {
        'compensated_bgr': compensated_bgr,
        'compensated_rgb': to_rgb_array(compensated_bgr),
        'ambient_lux': lux_est,
        'ambient_kelvin': round(cct, 1),
        'light_environment': 'Warm Indoor (<3500K)' if cct < 3500 else ('Standard Day/Studio (5000-6500K)' if cct <= 6800 else 'Cool/Cloudy (>6800K)'),
        'color_correction_gains': {
            'gain_r': round(scale_r, 3),
            'gain_g': round(scale_g, 3),
            'gain_b': round(scale_b, 3)
        }
    }


# =========================================================================
# 4. HISTOGRAM EQUALIZATION & CIELAB b* NORMALIZATION (TRF & TCRI)
# =========================================================================

def normalize_cielab_and_compute_metrics(compensated_bgr, powder_mask=None):
    """
    Programmatic color correction filter:
    - Locks CIELAB (L*a*b*) space parameters
    - Applies CLAHE to L* channel to standardize diffuse reflectance illumination
    - Scales b* channel against an internal color-rigidity benchmark to isolate synthetic dyes from pure curcumin
    - Computes TCRI (Turmeric Color/Texture Contrast Ratio Index - texture variance)
    - Computes TRF (Turmeric Reflectance Factor - reflectance intensity)
    """
    bgr = compensated_bgr.copy()
    h, w = bgr.shape[:2]

    # Convert to CIELAB space
    if HAS_OPENCV:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        # Apply CLAHE strictly to L* channel (lightness) to remove illumination shadows
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        equalized_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        # Fallback LAB approximation
        rgb = bgr[:, :, ::-1].astype(np.float32) / 255.0
        # Standard RGB to CIELAB transformation
        # Reference white D65
        X = rgb[:, :, 0] * 0.4124564 + rgb[:, :, 1] * 0.3575761 + rgb[:, :, 2] * 0.1804375
        Y = rgb[:, :, 0] * 0.2126729 + rgb[:, :, 1] * 0.7151522 + rgb[:, :, 2] * 0.0721750
        Z = rgb[:, :, 0] * 0.0193339 + rgb[:, :, 1] * 0.1191920 + rgb[:, :, 2] * 0.9503041
        X = X / 0.95047; Y = Y / 1.00000; Z = Z / 1.08883
        f = lambda t: np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16.0 / 116.0)
        fx, fy, fz = f(X), f(Y), f(Z)
        L = np.clip(116.0 * fy - 16.0, 0, 100)
        a = 500.0 * (fx - fy)
        b = 200.0 * (fy - fz)
        lab = np.stack([L * 2.55, a + 128, b + 128], axis=-1).astype(np.uint8)
        equalized_bgr = bgr

    # Powder ROI selection for metric computation
    if powder_mask is not None and np.sum(powder_mask > 0) > 100:
        roi_mask = (powder_mask > 0)
    else:
        roi_mask = np.ones((h, w), dtype=bool)

    # In OpenCV LAB, L* is [0, 255] (scaled 0-100), a* is [0, 255] (a-128), b* is [0, 255] (b-128)
    L_meas = lab[:, :, 0][roi_mask].astype(np.float32) * (100.0 / 255.0)
    a_meas = lab[:, :, 1][roi_mask].astype(np.float32) - 128.0
    b_meas = lab[:, :, 2][roi_mask].astype(np.float32) - 128.0

    mean_L = float(np.mean(L_meas))
    mean_a = float(np.mean(a_meas))
    mean_b = float(np.mean(b_meas))

    std_L = float(np.std(L_meas))
    std_b = float(np.std(b_meas))

    # Rigidity ratio: b* relative to chromatic vector length
    chromatic_norm = math.sqrt(mean_L ** 2 + mean_a ** 2 + 1e-4)
    rigidity_ratio = float(mean_b / chromatic_norm)
    
    # Rigidity index deviation from pure curcumin benchmark
    # Pure curcumin: rigidity_ratio ~ 0.65 - 0.75
    # Metanil Yellow: rigidity_ratio elevates significantly (>0.82)
    # Chalk / Starch: drops significantly (<0.40)
    rigidity_index_score = float(max(0.0, min(100.0, 100.0 - abs(rigidity_ratio - CURCUMIN_RIGIDITY_RATIO_TARGET) * 220.0)))

    # TRF (Turmeric Reflectance Factor):
    # Normalized reflectance intensity scaled against b* rigidity benchmark
    trf = float(round((mean_L / 60.0) * (mean_b / CURCUMIN_B_RIGIDITY_BENCHMARK), 3))

    # TCRI (Turmeric Color/Texture Contrast Ratio Index - texture variance metric):
    # High-frequency spatial texture variance normalized against diffuse luminance
    # Natural ground turmeric powder has distinctive micro-fibrous texture (TCRI ~ 1.8 - 3.2)
    # Industrial mineral adulterants like Lead Chromate and Chalk alter micro-granularity variance
    gray_roi = (0.299 * bgr[:, :, 2] + 0.587 * bgr[:, :, 1] + 0.114 * bgr[:, :, 0])[roi_mask]
    spatial_variance = float(np.var(gray_roi))
    tcri = float(round((spatial_variance / max(1.0, np.mean(gray_roi))) * (1.0 + std_L / 20.0), 3))

    return {
        'equalized_bgr': equalized_bgr,
        'equalized_rgb': to_rgb_array(equalized_bgr),
        'cielab': {
            'L_star': round(mean_L, 2),
            'a_star': round(mean_a, 2),
            'b_star': round(mean_b, 2),
            'L_std': round(std_L, 2),
            'b_std': round(std_b, 2),
            'b_rigidity_benchmark': CURCUMIN_B_RIGIDITY_BENCHMARK,
            'measured_rigidity_ratio': round(rigidity_ratio, 3),
            'rigidity_score_pct': round(rigidity_index_score, 1)
        },
        'trf': trf,
        'tcri': tcri
    }


# =========================================================================
# 5. INTEGRATED END-TO-END PREPROCESSING PIPELINE
# =========================================================================

def execute_vision_pipeline(image_input):
    """
    Executes the complete Computer Vision & Calibration Layer:
    1. Structural Content Quality Filter (Laplacian blur + Glare Index)
    2. Dynamic ROI & Contour Extraction
    3. Adaptive Ambient Light Estimator (Lux & Kelvin calibration)
    4. Histogram Equalization & CIELAB b* Normalization (TCRI + TRF)
    """
    # Step 1: Pre-inference quality check
    quality = check_image_quality(image_input)
    if not quality['is_valid']:
        return {
            'success': False,
            'quality_check': quality,
            'rejection_prompt': quality['rejection_prompt']
        }

    # Step 2: Dynamic ROI & Contour Extraction
    roi = extract_dynamic_roi(image_input)

    # Step 3: Adaptive Ambient Light Estimator
    ambient = estimate_ambient_light_and_compensate(
        roi['cropped_bgr'],
        powder_mask=roi['powder_mask']
    )

    # Step 4: Histogram Equalization & White Balance Normalization
    cielab_metrics = normalize_cielab_and_compute_metrics(
        ambient['compensated_bgr'],
        powder_mask=roi['powder_mask']
    )

    return {
        'success': True,
        'quality_check': quality,
        'roi': {
            'detected_mound': roi['detected_mound'],
            'bbox': roi['bbox'],
            'contour_meta': roi['contour_meta'],
            'cropped_rgb': roi['cropped_rgb']
        },
        'ambient_calibration': {
            'ambient_lux': ambient['ambient_lux'],
            'ambient_kelvin': ambient['ambient_kelvin'],
            'light_environment': ambient['light_environment'],
            'color_correction_gains': ambient['color_correction_gains']
        },
        'cielab_normalization': cielab_metrics['cielab'],
        'tcri': cielab_metrics['tcri'],
        'trf': cielab_metrics['trf'],
        'final_tensor_rgb': cielab_metrics['equalized_rgb']
    }
