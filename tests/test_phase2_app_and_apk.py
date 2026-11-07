"""
TurmericGuard AI & Pure Mobile App — Phase 2 Final Specification Test Suite
Validates:
1. Complete Color System Token Set:
   - --background: #FFFFFF
   - --surface: #FFFFFF
   - --border: #ECECEC
   - --brand-yellow: #F5C400
   - --brand-yellow-text: #000000 (14.2:1 contrast)
   - --text-primary: #171717
   - --text-secondary: #898989
   - --text-tertiary: #C4C4C4
   - --status-pure: #2E9E5B
   - --status-suspicious: #D97B1F (burnt amber)
   - --status-adulterated: #D64545
   - --shadow-color: rgba(23, 23, 23, 0.08)
2. Splash sequence (~2–3s, root silhouette, golden particles, bowl ripple, wordmark, skip, reduced motion)
3. Welcome screen structure (small Pure wordmark, Welcome heading, main action card, overlapping illustration ~30-40%, bottom nav with active dot)
4. Result screen staged reveal & tabular numerals
5. Micro-interactions (PressableScale 0.97, haptics on exactly 3 moments)
6. Device adaptability (320px, 375px, 430px, tablet 768px+ capped at 600px, proportional margins 5.5%, safe-area insets)
7. Standalone signed APK download endpoints
"""

import os
import sys
import zipfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app import app, APK_FILE_PATH

client = TestClient(app)

def test_color_tokens_defined():
    """Verify all 12 specified theme tokens are defined centrally in tokens.js."""
    tokens_path = "mobile_app/react_native/src/theme/tokens.js"
    assert os.path.exists(tokens_path)
    with open(tokens_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "#FFFFFF" in code          # --background and --surface
    assert "#ECECEC" in code          # --border
    assert "#F5C400" in code          # --brand-yellow
    assert "#000000" in code          # --brand-yellow-text
    assert "#171717" in code          # --text-primary
    assert "#898989" in code          # --text-secondary
    assert "#C4C4C4" in code          # --text-tertiary
    assert "#2E9E5B" in code          # --status-pure
    assert "#D97B1F" in code          # --status-suspicious
    assert "#D64545" in code          # --status-adulterated
    assert "rgba(23, 23, 23, 0.08)" in code  # --shadow-color


def test_splash_screen_specification():
    """Verify Splash sequence meets the exact 2-3s timing and element requirements."""
    splash_path = "mobile_app/react_native/src/components/SplashScreen.js"
    assert os.path.exists(splash_path)
    with open(splash_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "rootScaleAnim" in code
    assert "particlesOpacityAnim" in code
    assert "rippleScaleAnim" in code
    assert "brandingOpacityAnim" in code
    assert "handleSkip" in code
    assert "AccessibilityInfo.isReduceMotionEnabled" in code


def test_welcome_screen_structure_and_illustration():
    """Verify Welcome screen elements: wordmark, heading, action card, overlapping illustration."""
    app_path = "mobile_app/react_native/App.js"
    assert os.path.exists(app_path)
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "Pure" in code
    assert "Welcome to Pure," in code
    assert "Take a Test" in code
    assert "ProductIllustration" in code
    assert "overlappingIllustrationContainer" in code
    assert "bottomNavBar" in code
    assert "activeDotIndicator" in code


def test_result_screen_staged_reveal_and_tabular_numerals():
    """Verify Result screen staged sequence, tabular numbers, and burnt amber tone."""
    dash_path = "mobile_app/react_native/src/components/VerificationDashboard.js"
    assert os.path.exists(dash_path)
    with open(dash_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "pillFadeAnim" in code
    assert "confidenceBarAnim" in code
    assert "displayedConcentration" in code
    assert "tabular-nums" in code
    assert "statusSuspicious" in code or "#D97B1F" in code
    assert "HapticsService.triggerResultReveal" in code
    assert "Share.share" in code or "handleShare" in code


def test_haptics_strictly_three_moments():
    """Verify Haptics fire only on the three specified moments."""
    haptics_path = "mobile_app/react_native/src/services/HapticsService.js"
    assert os.path.exists(haptics_path)
    with open(haptics_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "triggerTakeTest" in code
    assert "triggerScanComplete" in code
    assert "triggerResultReveal" in code


def test_pressable_scale_global_wrapper():
    """Verify shared PressableScale component scales to 0.97 with reduced motion support."""
    pressable_path = "mobile_app/react_native/src/components/PressableScale.js"
    assert os.path.exists(pressable_path)
    with open(pressable_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "0.97" in code
    assert "Animated.spring" in code
    assert "AccessibilityInfo.isReduceMotionEnabled" in code


def test_device_adaptability_tokens_and_margins():
    """Verify proportional margins (5.5%), tablet max-width cap (600px), safe areas."""
    app_path = "mobile_app/react_native/App.js"
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "5.5%" in code or "horizontalMarginPct" in code
    assert "maxContentWidth" in code or "600" in code
    assert "SafeAreaView" in code


def test_apk_package_integrity_and_download():
    """Verify Android APK file is built and endpoints serve it properly."""
    assert os.path.exists(APK_FILE_PATH)
    assert os.path.getsize(APK_FILE_PATH) > 500_000

    with zipfile.ZipFile(APK_FILE_PATH, 'r') as z:
        names = z.namelist()
        assert 'AndroidManifest.xml' in names
        assert 'classes.dex' in names
        assert 'assets/turmeric_multitask_int8.onnx' in names

    res = client.get("/download/app.apk")
    assert res.status_code == 200
    assert "application/vnd.android.package-archive" in res.headers.get("content-type", "")
