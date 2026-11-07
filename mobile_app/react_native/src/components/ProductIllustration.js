/**
 * Pure — Product Illustration Component
 * 
 * An isolated, swappable vector illustration component designed to overlap
 * the main action card's lower edge by ~30–40%.
 * Features clean vector turmeric rhizome geometry and organic powder motif.
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Path, Circle, Defs, LinearGradient, Stop, G } from 'react-native-svg';
import { tokens } from '../theme/tokens';

export default function ProductIllustration({ width = 180, height = 120, style }) {
  return (
    <View style={[styles.container, style]} pointerEvents="none" accessibilityLabel="Turmeric powder product illustration">
      <Svg width={width} height={height} viewBox="0 0 180 120" fill="none">
        <Defs>
          {/* Subtle directional gradient conforming to top-left light source */}
          <LinearGradient id="moundGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor="#F5C400" />
            <Stop offset="55%" stopColor="#D97706" />
            <Stop offset="100%" stopColor="#92400E" />
          </LinearGradient>
          <LinearGradient id="bowlGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <Stop offset="0%" stopColor="#FFFFFF" />
            <Stop offset="100%" stopColor="#F1F5F9" />
          </LinearGradient>
        </Defs>

        {/* Soft Ground Shadow */}
        <Circle cx="90" cy="100" r="50" fill="rgba(23, 23, 23, 0.06)" />

        {/* Ceramic Sample Dish / Bowl */}
        <Path
          d="M30 85 C30 105 150 105 150 85 C150 78 30 78 30 85 Z"
          fill="url(#bowlGrad)"
          stroke={tokens.colors.border}
          strokeWidth="1"
        />

        {/* Turmeric Powder Mound with Micro-Texture */}
        <Path
          d="M48 84 C56 62 72 38 90 38 C108 38 124 62 132 84 C116 88 64 88 48 84 Z"
          fill="url(#moundGrad)"
        />

        {/* Apex Highlight */}
        <Circle cx="88" cy="46" r="14" fill="#F5C400" opacity="0.6" />

        {/* Floating Golden Micro-Particles */}
        <G fill={tokens.colors.brandYellow} opacity="0.85">
          <Circle cx="44" cy="48" r="3" />
          <Circle cx="136" cy="42" r="2.5" />
          <Circle cx="120" cy="24" r="3.5" />
          <Circle cx="64" cy="28" r="2" />
        </G>
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});

