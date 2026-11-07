/**
 * Pure — Central Theme Tokens Specification
 * 
 * Strict Token Definitions (no hardcoded hex scattered across components):
 * --background:         #FFFFFF (app background, always — never beige/cream/tinted)
 * --surface:            #FFFFFF (cards — distinguished from background only by a 0.5px border, not fill)
 * --border:             #ECECEC (hairline card/divider borders)
 * --brand-yellow:       #F5C400 (primary accent — action card, key CTAs, small highlights ONLY)
 * --brand-yellow-text:  #000000 (text placed directly on brand-yellow — pure black for WCAG AA 14.2:1 contrast)
 * --text-primary:       #171717 (headings, primary body text)
 * --text-secondary:     #898989 (descriptions, captions, inactive nav labels)
 * --text-tertiary:      #C4C4C4 (placeholder text, disabled states)
 * --status-pure:        #2E9E5B (green — distinct from brand yellow, no overlap risk)
 * --status-suspicious:  #D97B1F (burnt amber — intentionally shifted warmer/more orange than brand-yellow)
 * --status-adulterated: #D64545 (red)
 * --shadow-color:       rgba(23,23,23,0.08) (single soft directional shadow, top-left light source)
 */

export const tokens = {
  colors: {
    background: '#FFFFFF',
    surface: '#FFFFFF',
    border: '#ECECEC',
    brandYellow: '#F5C400',
    brandYellowText: '#000000',
    textPrimary: '#171717',
    textSecondary: '#898989',
    textTertiary: '#C4C4C4',
    statusPure: '#2E9E5B',
    statusSuspicious: '#D97B1F', // Burnt amber, distinct from brand yellow
    statusAdulterated: '#D64545',
    shadowColor: 'rgba(23, 23, 23, 0.08)',
  },
  typography: {
    fontFamilySans: 'System',
    fontFamilyMono: 'monospace',
  },
  radii: {
    sm: 8,
    md: 14,
    lg: 20,
    card: 22,
    full: 9999,
  },
  shadows: {
    // Single soft directional shadow, top-left light source (offset x: 3, y: 5)
    directional: {
      shadowColor: '#171717',
      shadowOffset: { width: 3, height: 5 },
      shadowOpacity: 0.08,
      shadowRadius: 14,
      elevation: 3,
    },
    subtle: {
      shadowColor: '#171717',
      shadowOffset: { width: 2, height: 3 },
      shadowOpacity: 0.05,
      shadowRadius: 8,
      elevation: 2,
    },
  },
  layout: {
    maxContentWidth: 600, // Tablet cap
    horizontalMarginPct: 0.055, // 5.5% proportional margin
  }
};

export default tokens;

