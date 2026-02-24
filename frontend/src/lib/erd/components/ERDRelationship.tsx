/**
 * ERDRelationship Component
 * Renders a relationship line between two tables - DBeaver style
 *
 * Features:
 * - Clean orthogonal paths with thin lines
 * - Simple dot markers at endpoints
 * - Cardinality labels (1, 1..n) near endpoints
 * - No shadows or bridge effects - lines just cross cleanly
 */

import type { ERDColors } from '../types';

interface ERDRelationshipProps {
  path: string;
  colors: ERDColors;
  isHighlighted: boolean;
  isSelected: boolean; // Whether any table is selected
  grayscaleEnabled: boolean; // Whether grayscale effect is enabled
  // Cardinality labels
  fromCardinality?: string; // e.g., "1", "0..1"
  toCardinality?: string;   // e.g., "1..n", "n"
  // Label positions (computed by parent)
  fromLabelPos?: { x: number; y: number };
  toLabelPos?: { x: number; y: number };
}

export function ERDRelationship({
  path,
  colors,
  isHighlighted,
  isSelected,
  grayscaleEnabled,
  fromCardinality = '1',
  toCardinality = '1..n',
  fromLabelPos,
  toLabelPos,
}: ERDRelationshipProps) {
  const strokeColor = isHighlighted ? colors.relationshipLineHighlight : colors.relationshipLine;
  // DBeaver uses thin lines - 1px normal, 1.5px highlighted
  const strokeWidth = isHighlighted ? 1.5 : 1;
  // White border is slightly wider than the main stroke
  const borderWidth = strokeWidth + 2;
  const shouldGrayscale = grayscaleEnabled && isSelected && !isHighlighted;

  return (
    <g filter={shouldGrayscale ? 'url(#grayscale)' : undefined}>
      {/* White border/outline - rendered first (behind) */}
      <path
        d={path}
        fill="none"
        stroke="white"
        strokeWidth={borderWidth}
        markerStart={isHighlighted ? 'url(#erd-dot-highlight-border)' : 'url(#erd-dot-border)'}
        markerEnd={isHighlighted ? 'url(#erd-dot-highlight-border)' : 'url(#erd-dot-border)'}
      />
      {/* Main relationship line - rendered on top */}
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        markerStart={isHighlighted ? 'url(#erd-dot-highlight)' : 'url(#erd-dot)'}
        markerEnd={isHighlighted ? 'url(#erd-dot-highlight)' : 'url(#erd-dot)'}
      />

      {/* Cardinality label at source - only show when highlighted or always visible */}
      {fromLabelPos && (
        <text
          x={fromLabelPos.x}
          y={fromLabelPos.y}
          fontSize="9"
          fill={colors.regularColumnText}
          textAnchor="middle"
          dominantBaseline="middle"
        >
          {fromCardinality}
        </text>
      )}

      {/* Cardinality label at target */}
      {toLabelPos && (
        <text
          x={toLabelPos.x}
          y={toLabelPos.y}
          fontSize="9"
          fill={colors.regularColumnText}
          textAnchor="middle"
          dominantBaseline="middle"
        >
          {toCardinality}
        </text>
      )}
    </g>
  );
}

