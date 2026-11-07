/**
 * TurmericGuard AI — Micro-Interaction Haptics Service
 * 
 * Strict Acceptance Criteria:
 * - Haptic feedback on exactly three moments:
 *   1. "Take a Test" tap (light impact)
 *   2. scan complete (medium impact)
 *   3. result reveal (light impact)
 * - Subtle single pulse only — never a repeating sequence or pattern.
 * - Does not fire globally on arbitrary clicks.
 */

import { Vibration, Platform } from 'react-native';

let expoHaptics = null;
try {
  // Optional dynamic require for expo-haptics if installed in client environment
  expoHaptics = require('expo-haptics');
} catch (e) {
  expoHaptics = null;
}

/**
 * Fires a single subtle light impact pulse (~10-15ms).
 * Used for:
 *  - "Take a Test" card tap
 *  - Result reveal moment
 */
export function triggerLightImpact() {
  try {
    if (expoHaptics && expoHaptics.impactAsync && expoHaptics.ImpactFeedbackStyle) {
      expoHaptics.impactAsync(expoHaptics.ImpactFeedbackStyle.Light);
      return;
    }
  } catch (err) {
    // continue to fallback
  }

  try {
    if (Platform.OS === 'web') {
      if (typeof window !== 'undefined' && window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(10);
      }
    } else {
      Vibration.vibrate(12);
    }
  } catch (err) {
    // Graceful no-op on non-vibrating platforms
  }
}

/**
 * Fires a single medium impact pulse (~25-30ms).
 * Used strictly for:
 *  - Scan complete moment
 */
export function triggerMediumImpact() {
  try {
    if (expoHaptics && expoHaptics.impactAsync && expoHaptics.ImpactFeedbackStyle) {
      expoHaptics.impactAsync(expoHaptics.ImpactFeedbackStyle.Medium);
      return;
    }
  } catch (err) {
    // continue to fallback
  }

  try {
    if (Platform.OS === 'web') {
      if (typeof window !== 'undefined' && window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(25);
      }
    } else {
      Vibration.vibrate(28);
    }
  } catch (err) {
    // Graceful no-op
  }
}

// Named semantic triggers strictly mapping to the three specified moments
export const HapticsService = {
  triggerTakeTest: () => triggerLightImpact(),
  triggerScanComplete: () => triggerMediumImpact(),
  triggerResultReveal: () => triggerLightImpact(),
};

export default HapticsService;

