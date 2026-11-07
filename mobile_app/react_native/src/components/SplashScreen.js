/**
 * Pure — Splash Sequence Component
 * 
 * Strict Phase 2 Animation Specification (~2–3s total):
 * 1. (0.0s) Clean white background.
 * 2. (0.0–0.8s) Simple turmeric-root SVG silhouette fades + scales in at center, soft ease-out, no bounce.
 * 3. (0.5–1.5s) 4–6 small golden particle shapes drift and fade in around it, slow and subtle.
 * 4. (1.2–2.0s) A flat white circle (bowl) appears below the root; a single mustard-yellow ripple arc animates outward once (not looping).
 * 5. (1.8–2.5s) Root/particles fade out; "Pure" wordmark + welcome heading fade/slide in from 12px below.
 * 6. (2.5–3.0s) Cross-fade into the Welcome screen.
 * 
 * - Visible Skip control from frame one.
 * - Full static fallback (final frame only, no animation) when `prefers-reduced-motion` is on.
 * - Animates only `transform` and `opacity`.
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  AccessibilityInfo,
  Platform
} from 'react-native';
import Svg, { Path, Circle } from 'react-native-svg';
import PressableScale from './PressableScale';
import { tokens } from '../theme/tokens';

export default function SplashScreen({ onFinish }) {
  const [reduceMotion, setReduceMotion] = useState(false);

  // Animation values (animating ONLY transform and opacity)
  const rootScaleAnim = useRef(new Animated.Value(0.85)).current;
  const rootOpacityAnim = useRef(new Animated.Value(0)).current;

  const particlesOpacityAnim = useRef(new Animated.Value(0)).current;
  const particlesTranslateY = useRef(new Animated.Value(10)).current;

  const bowlOpacityAnim = useRef(new Animated.Value(0)).current;
  const rippleScaleAnim = useRef(new Animated.Value(0.6)).current;
  const rippleOpacityAnim = useRef(new Animated.Value(0)).current;

  const brandingOpacityAnim = useRef(new Animated.Value(0)).current;
  const brandingTranslateY = useRef(new Animated.Value(12)).current;

  const fullContainerOpacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    let isMounted = true;
    if (AccessibilityInfo.isReduceMotionEnabled) {
      AccessibilityInfo.isReduceMotionEnabled()
        .then((enabled) => {
          if (isMounted && enabled) {
            setReduceMotion(true);
            // Instant fallback: skip directly to end
            onFinish();
          }
        })
        .catch(() => {});
    }

    if (reduceMotion) {
      onFinish();
      return;
    }

    // Choreographed 2.8s sequence
    const useNative = Platform.OS !== 'web';

    // Step 2: (0.0 - 0.8s) Root silhouette fades + scales in
    Animated.parallel([
      Animated.timing(rootOpacityAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: useNative,
      }),
      Animated.timing(rootScaleAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: useNative,
      }),
    ]).start();

    // Step 3: (0.5 - 1.5s) 4-6 golden particles drift in
    setTimeout(() => {
      if (!isMounted) return;
      Animated.parallel([
        Animated.timing(particlesOpacityAnim, {
          toValue: 1,
          duration: 900,
          useNativeDriver: useNative,
        }),
        Animated.timing(particlesTranslateY, {
          toValue: -8,
          duration: 1000,
          useNativeDriver: useNative,
        }),
      ]).start();
    }, 500);

    // Step 4: (1.2 - 2.0s) Bowl appears + single mustard-yellow ripple arc animates outward once
    setTimeout(() => {
      if (!isMounted) return;
      Animated.timing(bowlOpacityAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: useNative,
      }).start();

      Animated.sequence([
        Animated.timing(rippleOpacityAnim, {
          toValue: 0.9,
          duration: 250,
          useNativeDriver: useNative,
        }),
        Animated.parallel([
          Animated.timing(rippleScaleAnim, {
            toValue: 1.5,
            duration: 650,
            useNativeDriver: useNative,
          }),
          Animated.timing(rippleOpacityAnim, {
            toValue: 0,
            duration: 650,
            useNativeDriver: useNative,
          }),
        ])
      ]).start();
    }, 1200);

    // Step 5: (1.8 - 2.5s) Root/particles fade out; "Pure" wordmark fades & slides in from 12px below
    setTimeout(() => {
      if (!isMounted) return;
      Animated.parallel([
        Animated.timing(rootOpacityAnim, {
          toValue: 0,
          duration: 500,
          useNativeDriver: useNative,
        }),
        Animated.timing(particlesOpacityAnim, {
          toValue: 0,
          duration: 400,
          useNativeDriver: useNative,
        }),
        Animated.timing(bowlOpacityAnim, {
          toValue: 0,
          duration: 400,
          useNativeDriver: useNative,
        }),
        Animated.timing(brandingOpacityAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: useNative,
        }),
        Animated.timing(brandingTranslateY, {
          toValue: 0,
          duration: 600,
          useNativeDriver: useNative,
        }),
      ]).start();
    }, 1800);

    // Step 6: (2.6 - 3.0s) Cross-fade into welcome screen
    const finishTimer = setTimeout(() => {
      if (!isMounted) return;
      Animated.timing(fullContainerOpacity, {
        toValue: 0,
        duration: 350,
        useNativeDriver: useNative,
      }).start(() => {
        onFinish();
      });
    }, 2650);

    return () => {
      isMounted = false;
      clearTimeout(finishTimer);
    };
  }, [reduceMotion]);

  const handleSkip = () => {
    onFinish();
  };

  return (
    <Animated.View style={[styles.container, { opacity: fullContainerOpacity }]}>
      {/* Visible Skip control from frame one */}
      <View style={styles.skipContainer}>
        <PressableScale
          style={styles.skipButton}
          onPress={handleSkip}
          accessibilityLabel="Skip splash intro"
          accessibilityRole="button"
        >
          <Text style={styles.skipText}>Skip</Text>
        </PressableScale>
      </View>

      {/* Visual Animation Stage */}
      <View style={styles.stageArea}>
        {/* Lottie Drop-in Slot Annotation: LOTTIE_ANIMATION_SLOT */}

        {/* 1. Centered Turmeric Root SVG Silhouette */}
        <Animated.View
          style={[
            styles.rootWrapper,
            {
              opacity: rootOpacityAnim,
              transform: [{ scale: rootScaleAnim }],
            }
          ]}
        >
          <Svg width={110} height={110} viewBox="0 0 100 100" fill="none">
            {/* Minimal geometric turmeric root silhouette */}
            <Path
              d="M45 20 C60 18 78 28 82 45 C86 60 76 75 60 82 C44 88 28 80 22 65 C16 50 25 32 45 20 Z"
              fill={tokens.colors.brandYellow}
            />
            {/* Subtle rhizome lateral branch */}
            <Path
              d="M32 48 C20 45 14 55 18 64 C22 72 32 68 34 60 Z"
              fill={tokens.colors.brandYellow}
              opacity={0.88}
            />
          </Svg>
        </Animated.View>

        {/* 2. Floating Golden Particles (4-6 particles) */}
        <Animated.View
          style={[
            styles.particlesWrapper,
            {
              opacity: particlesOpacityAnim,
              transform: [{ translateY: particlesTranslateY }],
            }
          ]}
        >
          <View style={[styles.particleDot, { top: 20, left: 30, width: 6, height: 6 }]} />
          <View style={[styles.particleDot, { top: 35, right: 28, width: 5, height: 5 }]} />
          <View style={[styles.particleDot, { bottom: 30, left: 45, width: 7, height: 7 }]} />
          <View style={[styles.particleDot, { bottom: 42, right: 36, width: 4, height: 4 }]} />
          <View style={[styles.particleDot, { top: 60, left: 18, width: 5, height: 5 }]} />
        </Animated.View>

        {/* 3. Flat White Circle (Bowl) with Single Ripple Arc */}
        <Animated.View
          style={[
            styles.bowlWrapper,
            {
              opacity: bowlOpacityAnim,
            }
          ]}
        >
          <View style={styles.whiteBowlCircle} />
          {/* Animated Mustard-Yellow Ripple Arc */}
          <Animated.View
            style={[
              styles.rippleArc,
              {
                opacity: rippleOpacityAnim,
                transform: [{ scale: rippleScaleAnim }],
              }
            ]}
          />
        </Animated.View>

        {/* 4. "Pure" Wordmark + Welcome Heading fading/sliding from 12px below */}
        <Animated.View
          style={[
            styles.brandingWrapper,
            {
              opacity: brandingOpacityAnim,
              transform: [{ translateY: brandingTranslateY }],
            }
          ]}
        >
          <Text style={styles.brandWordmark}>Pure</Text>
          <Text style={styles.brandSubheading}>Turmeric Authenticity Auditor</Text>
        </Animated.View>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: tokens.colors.background, // Pure white background
    zIndex: 1000,
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 48,
  },
  skipContainer: {
    width: '100%',
    alignItems: 'flex-end',
    paddingHorizontal: 28,
  },
  skipButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: 'rgba(23, 23, 23, 0.04)',
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
  },
  skipText: {
    fontSize: 13,
    fontWeight: '600',
    color: tokens.colors.textSecondary,
  },
  stageArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    width: 280,
    height: 280,
  },
  rootWrapper: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  particlesWrapper: {
    ...StyleSheet.absoluteFillObject,
    pointerEvents: 'none',
  },
  particleDot: {
    position: 'absolute',
    borderRadius: 999,
    backgroundColor: tokens.colors.brandYellow,
    opacity: 0.85,
  },
  bowlWrapper: {
    position: 'absolute',
    bottom: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  whiteBowlCircle: {
    width: 80,
    height: 30,
    borderRadius: 40,
    backgroundColor: tokens.colors.surface,
    borderWidth: 1,
    borderColor: tokens.colors.border,
  },
  rippleArc: {
    position: 'absolute',
    width: 90,
    height: 90,
    borderRadius: 45,
    borderWidth: 2,
    borderColor: tokens.colors.brandYellow,
  },
  brandingWrapper: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandWordmark: {
    fontSize: 44,
    fontWeight: '900',
    color: tokens.colors.textPrimary,
    letterSpacing: -1,
  },
  brandSubheading: {
    fontSize: 13,
    fontWeight: '500',
    color: tokens.colors.textSecondary,
    marginTop: 4,
    letterSpacing: 0.2,
  },
});

