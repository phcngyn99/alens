/**
 * ERDMarkers Component
 * SVG marker definitions for relationship lines
 *
 * Design: DBeaver-style minimal markers - just small connection dots
 */

import type { ERDColors } from '../types';

interface ERDMarkersProps {
  colors: ERDColors;
  grayscaleOpacity: number;
}

export function ERDMarkers({ colors, grayscaleOpacity }: ERDMarkersProps) {
  return (
    <defs>
      {/* White border markers - rendered first (behind) */}
      <marker id="erd-dot-border" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
        <rect x="0" y="0" width="8" height="8" fill="white" />
      </marker>
      <marker id="erd-dot-highlight-border" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
        <rect x="0" y="0" width="8" height="8" fill="white" />
      </marker>

      {/* Minimal dot marker for connection points - DBeaver style */}
      <marker id="erd-dot" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
        <rect x="1" y="1" width="4" height="4" fill={colors.relationshipMarker} />
      </marker>
      <marker id="erd-dot-highlight" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
        <rect x="1" y="1" width="4" height="4" fill={colors.relationshipMarkerHighlight} />
      </marker>

      {/* Subtle selection highlight - no heavy shadows */}
      <filter id="selected-glow" x="-10%" y="-10%" width="120%" height="120%">
        <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor={colors.selectedShadow} floodOpacity="0.6" />
      </filter>

      {/* Grayscale filter for unrelated tables and lines with configurable opacity */}
      <filter id="grayscale">
        <feColorMatrix type="saturate" values="0" />
        <feComponentTransfer>
          <feFuncA type="linear" slope={grayscaleOpacity} />
        </feComponentTransfer>
      </filter>
    </defs>
  );
}

