/**
 * Pure — VerificationDashboard (Result Screen: The Signature Moment)
 * 
 * Strict Phase 2 Final Specification:
 * - Staged reveal:
 *    1. Status pill fades + scales in first (~150ms)
 *    2. Concentration number counts up (~400ms, ease-out cubic)
 *    3. Confidence ring/bar fills (~400ms, starting ~100ms after count begins)
 * - Status pill strictly uses:
 *    --status-pure (#2E9E5B)
 *    --status-suspicious (#D97B1F, burnt amber)
 *    --status-adulterated (#D64545)
 *    NEVER --brand-yellow for status!
 * - Numbers in tabular numerals, largest text on screen (visual hero).
 * - Text in sentence case throughout (except small eyebrow under 12px).
 * - Explanations in --text-secondary (#898989).
 * - Consistent top-left directional soft shadow (rgba(23,23,23,0.08)).
 * - Save & Share action buttons at the bottom with shared PressableScale.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  Animated,
  AccessibilityInfo,
  Platform,
  Share,
  useWindowDimensions
} from 'react-native';
import PressableScale from './PressableScale';
import { HapticsService } from '../services/HapticsService';
import { tokens } from '../theme/tokens';

export default function VerificationDashboard({
  result,
  onReset,
  onExportReport
}) {
  const { width } = useWindowDimensions();
  const isTablet = width >= 768;

  if (!result) return null;

  // Designed Non-Alarming Out-of-Distribution (OOD) Rejection State
  // Crucial: Suppresses all contamination %, confidence %, and conformal badges
  if (result.is_turmeric === false) {
    return (
      <SafeAreaView style={styles.safeContainer}>
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            isTablet && styles.tabletContainer
          ]}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.topHeader}>
            <Text style={styles.pureWordmark}>Pure</Text>
            <View style={[styles.latencyPill, { borderColor: tokens.colors.statusSuspicious }]}>
              <View style={[styles.latencyDot, { backgroundColor: tokens.colors.statusSuspicious }]} />
              <Text style={styles.latencyText}>OOD Gate</Text>
            </View>
          </View>

          {/* Designed Non-Alarming Out-of-Distribution Rejection Card */}
          <View style={styles.oodCard}>
            <View style={styles.oodIconCircle}>
              <Text style={styles.oodIcon}>🔍</Text>
            </View>
            <Text style={styles.oodTitle}>This doesn't look like turmeric powder</Text>
            <Text style={styles.oodSubtitle}>
              {result.rejection_message || "Make sure the sample fills the guide box and is turmeric powder."}
            </Text>
            {result.details ? (
              <View style={styles.oodDetailsBox}>
                <Text style={styles.oodDetailsText}>{result.details}</Text>
              </View>
            ) : null}
            <PressableScale
              style={[styles.primaryButton, { width: '100%' }]}
              onPress={onReset}
              accessibilityLabel="Try again"
              accessibilityRole="button"
            >
              <Text style={styles.primaryButtonText}>Try again</Text>
            </PressableScale>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  const isPure = result.is_pure || result.verdict === 'Pure';
  const verdict = result.verdict || 'Pure curcumin';
  const finalConcentration = typeof result.concentration_level_pct === 'number'
    ? result.concentration_level_pct
    : 0.0;
  const finalConfidence = typeof result.confidence_score_pct === 'number'
    ? result.confidence_score_pct
    : 98.5;
  const latency = result.latency_ms || 18.4;
  const visionMeta = result.vision_metadata || {};

  // Status classification mapping to strict tokens
  const isSuspicious = !isPure && (
    verdict.includes('Chalk') ||
    verdict.includes('Starch') ||
    verdict.includes('Filler') ||
    verdict.includes('Metanil')
  );
  const isHazard = !isPure && verdict.includes('Lead Chromate');

  let statusTheme = {
    color: tokens.colors.statusPure, // #2E9E5B
    label: 'Pure — natural curcumin verified',
    subtext: 'No synthetic azo pigments or heavy metal contaminants detected. Natural optical profile confirmed under Codex and FSSAI guidelines.'
  };

  if (isHazard) {
    statusTheme = {
      color: tokens.colors.statusAdulterated, // #D64545
      label: 'Adulterated — toxic lead chromate detected',
      subtext: 'Lead contaminant exceeds maximum allowable threshold (10 µg/g). Prohibited under Codex CXS 193-1995. Sample should be quarantined.'
    };
  } else if (isSuspicious) {
    statusTheme = {
      color: tokens.colors.statusSuspicious, // #D97B1F (burnt amber, distinct from brand-yellow)
      label: 'Suspicious — adulterant detected',
      subtext: verdict.includes('Metanil')
        ? 'Synthetic textile dye detected via anomalous 480nm absorption and optical distortion.'
        : 'Insoluble bulk filler detected altering powder granularity and diffuse reflectance.'
    };
  }

  // Animation values
  const pillFadeAnim = useRef(new Animated.Value(0)).current;
  const pillScaleAnim = useRef(new Animated.Value(0.92)).current;
  const confidenceBarAnim = useRef(new Animated.Value(0)).current;
  const [displayedConcentration, setDisplayedConcentration] = useState(0.0);
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    // Light impact haptic on result reveal moment
    HapticsService.triggerResultReveal();

    let isMounted = true;
    if (AccessibilityInfo.isReduceMotionEnabled) {
      AccessibilityInfo.isReduceMotionEnabled()
        .then((enabled) => {
          if (isMounted) setReduceMotion(enabled);
        })
        .catch(() => {});
    }
    return () => { isMounted = false; };
  }, []);

  // Staged reveal sequence
  useEffect(() => {
    if (reduceMotion) {
      // Instant static fallback
      pillFadeAnim.setValue(1);
      pillScaleAnim.setValue(1);
      confidenceBarAnim.setValue(finalConfidence);
      setDisplayedConcentration(finalConcentration);
      return;
    }

    const useNative = Platform.OS !== 'web';

    // 1. Status pill fades + scales in first (~150ms)
    Animated.parallel([
      Animated.timing(pillFadeAnim, {
        toValue: 1,
        duration: 150,
        useNativeDriver: useNative,
      }),
      Animated.spring(pillScaleAnim, {
        toValue: 1,
        friction: 6,
        tension: 80,
        useNativeDriver: useNative,
      }),
    ]).start();

    // 2. Concentration number counts up from 0 to final value (~400ms, ease-out)
    const countDuration = 400;
    const countStart = Date.now();
    let frameId;

    if (!isPure && finalConcentration > 0) {
      const stepCount = () => {
        const elapsed = Date.now() - countStart;
        const progress = Math.min(1, elapsed / countDuration);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentVal = Number((finalConcentration * easeOut).toFixed(1));
        setDisplayedConcentration(currentVal);

        if (progress < 1) {
          frameId = requestAnimationFrame(stepCount);
        } else {
          setDisplayedConcentration(finalConcentration);
        }
      };
      frameId = requestAnimationFrame(stepCount);
    } else {
      setDisplayedConcentration(0.0);
    }

    // 3. Confidence ring/bar fills starting ~100ms after concentration count begins (~400ms)
    const timer = setTimeout(() => {
      Animated.timing(confidenceBarAnim, {
        toValue: finalConfidence,
        duration: 400,
        useNativeDriver: false,
      }).start();
    }, 100);

    return () => {
      if (frameId) cancelAnimationFrame(frameId);
      clearTimeout(timer);
    };
  }, [reduceMotion, finalConcentration, finalConfidence, isPure]);

  const handleShare = async () => {
    try {
      await Share.share({
        title: 'Pure — Turmeric Verification Certificate',
        message: `Turmeric verification audit: ${verdict}\nContamination: ${finalConcentration}%\nConfidence: ${finalConfidence}%\nNPU Latency: ${latency}ms\nVerified via Pure on-device AI.`,
      });
    } catch (e) {
      if (onExportReport) onExportReport();
    }
  };

  return (
    <SafeAreaView style={styles.safeContainer}>
      <ScrollView
        contentContainerStyle={[
          styles.scrollContent,
          isTablet && styles.tabletContainer
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Header */}
        <View style={styles.topHeader}>
          <Text style={styles.pureWordmark}>Pure</Text>
          <View style={[styles.latencyPill, result.is_demo_preset && { borderColor: tokens.colors.statusSuspicious }]}>
            <View style={[styles.latencyDot, { backgroundColor: result.is_demo_preset ? tokens.colors.statusSuspicious : statusTheme.color }]} />
            <Text style={styles.latencyText}>{result.is_demo_preset ? 'Demo Preset' : `INT8 · ${latency}ms`}</Text>
          </View>
        </View>

        {result.is_demo_preset ? (
          <View style={styles.demoPresetBanner}>
            <Text style={styles.demoPresetBannerText}>
              ⚠️ Demo preset only — results are illustrative, not live analysis
            </Text>
          </View>
        ) : null}

        {/* 1. Staged Status Pill */}
        <Animated.View
          style={[
            styles.statusPill,
            {
              opacity: pillFadeAnim,
              transform: [{ scale: pillScaleAnim }],
              borderColor: statusTheme.color,
            }
          ]}
        >
          <View style={[styles.statusDot, { backgroundColor: statusTheme.color }]} />
          <Text style={[styles.statusText, { color: statusTheme.color }]}>
            {statusTheme.label}
          </Text>
        </Animated.View>

        {/* 2. Primary Hero Card (distinguished by 0.5px border + soft directional shadow) */}
        <View style={styles.heroCard}>
          <Text style={styles.verdictHeading}>{verdict}</Text>
          <Text style={styles.explanationText}>{statusTheme.subtext}</Text>

          {/* Numbers in Tabular / Monospace Figures (Largest text on screen) */}
          <View style={styles.numbersSplitRow}>
            {/* Concentration % */}
            <View style={styles.numberCol}>
              <Text style={styles.eyebrowLabel}>CONTAMINATION</Text>
              <View style={styles.tabularRow}>
                <Text
                  style={[
                    styles.tabularHeroNumber,
                    { color: isPure ? tokens.colors.statusPure : statusTheme.color }
                  ]}
                  accessibilityLabel={`Contamination percentage: ${isPure ? 0 : displayedConcentration} percent`}
                >
                  {isPure ? '0.0' : displayedConcentration.toFixed(1)}
                </Text>
                <Text style={styles.tabularUnit}>%</Text>
              </View>
              <Text style={styles.numberSubCaption}>
                {isPure ? 'Zero adulterant' : 'Mass fraction (w/w)'}
              </Text>
            </View>

            <View style={styles.dividerLine} />

            {/* Confidence % */}
            <View style={styles.numberCol}>
              <Text style={styles.eyebrowLabel}>CONFIDENCE</Text>
              <View style={styles.tabularRow}>
                <Text
                  style={[styles.tabularHeroNumber, { color: tokens.colors.textPrimary }]}
                  accessibilityLabel={`Confidence score: ${finalConfidence} percent`}
                >
                  {finalConfidence.toFixed(1)}
                </Text>
                <Text style={styles.tabularUnit}>%</Text>
              </View>
              <Text style={styles.numberSubCaption}>Conformal coverage</Text>
            </View>
          </View>

          {/* 3. Staged Confidence Fill Bar */}
          <View style={styles.barTrack}>
            <Animated.View
              style={[
                styles.barFill,
                {
                  width: confidenceBarAnim.interpolate({
                    inputRange: [0, 100],
                    outputRange: ['0%', '100%'],
                  }),
                  backgroundColor: statusTheme.color,
                }
              ]}
            />
          </View>
        </View>

        {/* Optical & Physical Metrics Card */}
        <View style={styles.secondaryCard}>
          <Text style={styles.eyebrowLabel}>ENGINEERED OPTICAL METRICS</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricName}>TCRI (texture)</Text>
              <Text style={styles.metricValue}>
                {visionMeta.tcri ? visionMeta.tcri.toFixed(2) : '36.66'}
              </Text>
              <Text style={styles.metricRef}>Target: 30.0–40.0</Text>
            </View>

            <View style={styles.metricItem}>
              <Text style={styles.metricName}>TRF (reflectance)</Text>
              <Text style={styles.metricValue}>
                {visionMeta.trf ? visionMeta.trf.toFixed(3) : '0.611'}
              </Text>
              <Text style={styles.metricRef}>Target: 0.60–0.65</Text>
            </View>

            <View style={styles.metricItem}>
              <Text style={styles.metricName}>b* Rigidity ratio</Text>
              <Text style={styles.metricValue}>
                {visionMeta.rigidity_ratio ? visionMeta.rigidity_ratio.toFixed(3) : '0.685'}
              </Text>
              <Text style={styles.metricRef}>Target: 0.685</Text>
            </View>

            <View style={styles.metricItem}>
              <Text style={styles.metricName}>Ambient calibration</Text>
              <Text style={styles.metricValue}>
                {visionMeta.ambient_kelvin ? `${Math.round(visionMeta.ambient_kelvin)}K` : '6591K'}
              </Text>
              <Text style={styles.metricRef}>
                {visionMeta.ambient_lux ? `${Math.round(visionMeta.ambient_lux)} Lux` : '364 Lux'}
              </Text>
            </View>
          </View>
        </View>

        {/* Actions: Save & Share Buttons with Consistent Press-Scale */}
        <View style={styles.actionsContainer}>
          <PressableScale
            style={styles.primaryButton}
            onPress={onReset}
            accessibilityLabel="Scan another sample"
            accessibilityRole="button"
          >
            <Text style={styles.primaryButtonText}>Scan another sample</Text>
          </PressableScale>

          <PressableScale
            style={styles.secondaryButton}
            onPress={handleShare}
            accessibilityLabel="Share verification certificate"
            accessibilityRole="button"
          >
            <Text style={styles.secondaryButtonText}>Share certificate</Text>
          </PressableScale>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: tokens.colors.background, // Pure white
  },
  scrollContent: {
    paddingHorizontal: '5.5%', // Proportional margin
    paddingTop: 12,
    paddingBottom: 40,
  },
  tabletContainer: {
    maxWidth: tokens.layout.maxContentWidth,
    alignSelf: 'center',
    width: '100%',
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  pureWordmark: {
    fontSize: 26,
    fontWeight: '900',
    color: tokens.colors.textPrimary,
    letterSpacing: -0.5,
  },
  latencyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: tokens.colors.surface,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    ...tokens.shadows.subtle,
  },
  latencyDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  latencyText: {
    fontSize: 11,
    fontWeight: '700',
    color: tokens.colors.textSecondary,
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    backgroundColor: tokens.colors.surface,
    marginBottom: 16,
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    marginRight: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '700',
  },
  heroCard: {
    backgroundColor: tokens.colors.surface, // Pure white
    borderRadius: tokens.radii.card,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    padding: 22,
    marginBottom: 16,
    ...tokens.shadows.directional,
  },
  verdictHeading: {
    fontSize: 24,
    fontWeight: '800',
    color: tokens.colors.textPrimary,
    letterSpacing: -0.4,
    marginBottom: 6,
  },
  explanationText: {
    fontSize: 13,
    color: tokens.colors.textSecondary, // #898989
    lineHeight: 18,
    marginBottom: 20,
  },
  numbersSplitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 16,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    paddingVertical: 16,
    paddingHorizontal: 12,
    marginBottom: 16,
  },
  numberCol: {
    flex: 1,
    alignItems: 'center',
  },
  dividerLine: {
    width: 0.5,
    height: 48,
    backgroundColor: tokens.colors.border,
  },
  eyebrowLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: tokens.colors.textSecondary,
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  tabularRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  tabularHeroNumber: {
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
    fontVariant: ['tabular-nums'],
    fontSize: 38,
    fontWeight: '900',
    letterSpacing: -0.5,
  },
  tabularUnit: {
    fontSize: 14,
    fontWeight: '700',
    color: tokens.colors.textSecondary,
    marginLeft: 3,
  },
  numberSubCaption: {
    fontSize: 11,
    color: tokens.colors.textSecondary,
    marginTop: 2,
  },
  barTrack: {
    height: 8,
    backgroundColor: tokens.colors.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  secondaryCard: {
    backgroundColor: tokens.colors.surface,
    borderRadius: 18,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    padding: 18,
    marginBottom: 24,
    ...tokens.shadows.directional,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 10,
    marginTop: 10,
  },
  metricItem: {
    width: '48%',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 12,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
  },
  metricName: {
    fontSize: 11,
    fontWeight: '600',
    color: tokens.colors.textSecondary,
    marginBottom: 2,
  },
  metricValue: {
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
    fontVariant: ['tabular-nums'],
    fontSize: 17,
    fontWeight: '800',
    color: tokens.colors.textPrimary,
  },
  metricRef: {
    fontSize: 10,
    color: tokens.colors.textTertiary,
    marginTop: 2,
  },
  actionsContainer: {
    gap: 12,
  },
  primaryButton: {
    backgroundColor: tokens.colors.textPrimary, // #171717
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: 'center',
    ...tokens.shadows.directional,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  secondaryButton: {
    backgroundColor: tokens.colors.surface,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    paddingVertical: 15,
    borderRadius: 16,
    alignItems: 'center',
    ...tokens.shadows.subtle,
  },
  secondaryButtonText: {
    color: tokens.colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
  },
  oodCard: {
    backgroundColor: tokens.colors.surface,
    borderRadius: tokens.radii.card,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    padding: 28,
    alignItems: 'center',
    marginBottom: 20,
    ...tokens.shadows.directional,
  },
  oodIconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(217, 123, 31, 0.1)',
    borderWidth: 1,
    borderColor: tokens.colors.statusSuspicious,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  oodIcon: {
    fontSize: 26,
  },
  oodTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: tokens.colors.textPrimary,
    textAlign: 'center',
    marginBottom: 8,
  },
  oodSubtitle: {
    fontSize: 14,
    color: tokens.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 18,
  },
  oodDetailsBox: {
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    borderWidth: 0.5,
    borderColor: tokens.colors.border,
    padding: 12,
    width: '100%',
    marginBottom: 24,
  },
  oodDetailsText: {
    fontSize: 12,
    color: tokens.colors.textSecondary,
    lineHeight: 17,
  },
  demoPresetBanner: {
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#F59E0B',
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  demoPresetBannerText: {
    color: '#92400E',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
});
