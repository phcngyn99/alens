/**
 * ERD Library Default Configuration
 * Default values for colors, layout, zoom, and feature flags
 */

import type { ERDColors, ERDLayoutConfig, ERDZoomConfig, ERDConfig, ERDEffectsSettings } from './types';

// ============================================================================
// Default Colors (Light Theme - DBeaver-inspired clean design)
// ============================================================================

export const DEFAULT_COLORS: ERDColors = {
  // Backgrounds - clean light theme
  containerBg: '#f8fafc',
  tableBg: '#ffffff',
  tableHeaderBg: '#3b82f6',  // DBeaver uses blue headers
  tableSelectedHeaderBg: '#1d4ed8',  // Darker blue when selected
  expandButtonBg: '#f1f5f9',
  expandButtonHoverBg: '#e2e8f0',
  pkRowBg: '#22c55e',  // Green for primary key indicator

  // Borders - subtle and clean
  containerBorder: '#e2e8f0',
  tableBorder: '#94a3b8',
  tableSelectedBorder: '#3b82f6',
  tableConnectedBorder: '#60a5fa',

  // Text
  tableNameText: '#ffffff',  // White text on blue header
  tableSelectedNameText: '#ffffff',
  pkText: '#166534',  // Dark green for PK columns
  fkText: '#0891b2',  // Cyan for FK columns
  regularColumnText: '#475569',
  expandButtonText: '#64748b',

  // Relationship lines - subtle gray/blue
  relationshipLine: '#64748b',
  relationshipLineHighlight: '#3b82f6',
  relationshipMarker: '#64748b',
  relationshipMarkerHighlight: '#3b82f6',

  // Selection - subtle glow
  selectedShadow: 'rgba(59, 130, 246, 0.4)',
  connectedShadow: 'rgba(96, 165, 250, 0.2)',
};

// ============================================================================
// Default Layout Configuration
// ============================================================================

export const DEFAULT_LAYOUT: ERDLayoutConfig = {
  nodeWidth: 160,
  headerHeight: 26,
  columnHeight: 18,
  horizontalGap: 60,
  verticalGap: 30,
  columnsPerRow: 0, // 0 means auto-calculate based on table count
};

// ============================================================================
// Default Zoom Configuration
// ============================================================================

export const DEFAULT_ZOOM: ERDZoomConfig = {
  minScale: 1.0,
  maxScale: 2.0,
  zoomStep: 0.1,
};

// ============================================================================
// Default Effects Configuration
// ============================================================================

export const DEFAULT_EFFECTS: ERDEffectsSettings = {
  grayscale: {
    enabled: true,
    opacity: 0.25, // 25% opacity for grayscale elements
  },
  bridgeSize: 6,
};

// ============================================================================
// Default ERD Configuration
// ============================================================================

export const DEFAULT_CONFIG: ERDConfig = {
  colors: DEFAULT_COLORS,
  layout: DEFAULT_LAYOUT,
  zoom: DEFAULT_ZOOM,
  effects: DEFAULT_EFFECTS,

  // Feature flags
  enablePanZoom: true,
  enableDragging: true,
  enableSelection: true,
  enableExpand: true,
  enableSave: false,
};

/**
 * Merge partial config with defaults
 */
export function mergeConfig(partial?: Partial<ERDConfig>): ERDConfig {
  if (!partial) return DEFAULT_CONFIG;

  return {
    ...DEFAULT_CONFIG,
    ...partial,
    colors: partial.colors ? { ...DEFAULT_COLORS, ...partial.colors } : DEFAULT_COLORS,
    layout: partial.layout ? { ...DEFAULT_LAYOUT, ...partial.layout } : DEFAULT_LAYOUT,
    zoom: partial.zoom ? { ...DEFAULT_ZOOM, ...partial.zoom } : DEFAULT_ZOOM,
    effects: partial.effects ? {
      ...DEFAULT_EFFECTS,
      ...partial.effects,
      grayscale: partial.effects.grayscale ? {
        ...DEFAULT_EFFECTS.grayscale,
        ...partial.effects.grayscale,
      } : DEFAULT_EFFECTS.grayscale,
    } : DEFAULT_EFFECTS,
  };
}

