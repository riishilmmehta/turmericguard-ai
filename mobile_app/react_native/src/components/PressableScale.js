/**
 * Pure — Shared PressableScale Wrapper Component
 * 
 * Provides consistent tactile micro-interaction across all tappable elements:
 * - Scales down to 0.97 on press-in (~100ms)
 * - Springs smoothly back to 1.0 on release (~100ms)
 * - Automatically respects system reduced-motion preference (falls back to static 1.0)
 * - Accepts all standard Pressable / TouchableOpacity props & accessibility tags
 */

import React, { useRef, useState, useEffect } from 'react';
import {
  Pressable,
  Animated,
  StyleSheet,
  AccessibilityInfo,
  Platform
} from 'react-native';

export default function PressableScale({
  children,
  style,
  onPress,
  onPressIn,
  onPressOut,
  disabled = false,
  scaleTo = 0.97,
  duration = 100,
  accessibilityLabel,
  accessibilityRole = 'button',
  accessibilityHint,
  testID,
  ...restProps
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    let isMounted = true;
    if (AccessibilityInfo.isReduceMotionEnabled) {
      AccessibilityInfo.isReduceMotionEnabled()
        .then((enabled) => {
          if (isMounted) setReduceMotion(enabled);
        })
        .catch(() => {});
    }

    const sub = AccessibilityInfo.addEventListener
      ? AccessibilityInfo.addEventListener('reduceMotionChanged', (enabled) => {
          if (isMounted) setReduceMotion(enabled);
        })
      : null;

    return () => {
      isMounted = false;
      if (sub && sub.remove) sub.remove();
    };
  }, []);

  const handlePressIn = (event) => {
    if (disabled) return;
    if (!reduceMotion) {
      Animated.timing(scaleAnim, {
        toValue: scaleTo,
        duration: duration,
        useNativeDriver: Platform.OS !== 'web',
      }).start();
    }
    if (onPressIn) onPressIn(event);
  };

  const handlePressOut = (event) => {
    if (disabled) return;
    if (!reduceMotion) {
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 5,
        tension: 100,
        useNativeDriver: Platform.OS !== 'web',
      }).start();
    }
    if (onPressOut) onPressOut(event);
  };

  return (
    <Pressable
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled}
      accessibilityRole={accessibilityRole}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      testID={testID}
      {...restProps}
    >
      <Animated.View
        style={[
          style,
          !reduceMotion && {
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        {children}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({});

