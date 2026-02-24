/**
 * ERD Library Types
 * Reusable type definitions for Entity-Relationship Diagram components
 */

import type { Table, ForeignKey } from '../../types';

// ============================================================================
// Core Data Types
// ============================================================================

/** Position of a node in the diagram */
export interface Position {
  x: number;
  y: number;
}

/** Transform state for pan/zoom */
export interface Transform {
  x: number;
  y: number;
  scale: number;
}

/** A table node in the ERD */
export interface ERDNode {
  id: string;
  table: Table;
  x: number;
  y: number;
  width: number;
  height: number;
}

/** A relationship/connection between two tables */
export interface ERDRelationship {
  id: string;
  fromTable: string;
  fromColumn: string;
  toTable: string;
  toColumn: string;
  foreignKey?: ForeignKey;
}

/** Path segment for line crossing detection */
export interface PathSegment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  isVertical: boolean;
}

/** A crossing point between two lines */
export interface CrossingPoint {
  x: number;
  y: number;
}

// ============================================================================
// Configuration Types
// ============================================================================

/** Color configuration for the ERD */
export interface ERDColors {
  // Backgrounds
  containerBg: string;
  tableBg: string;
  tableHeaderBg: string;
  tableSelectedHeaderBg: string;
  expandButtonBg: string;
  expandButtonHoverBg: string;
  pkRowBg: string;

  // Borders
  containerBorder: string;
  tableBorder: string;
  tableSelectedBorder: string;
  tableConnectedBorder: string;

  // Text
  tableNameText: string;
  tableSelectedNameText: string;
  pkText: string;
  fkText: string;
  regularColumnText: string;
  expandButtonText: string;

  // Relationship lines
  relationshipLine: string;
  relationshipLineHighlight: string;
  relationshipMarker: string;
  relationshipMarkerHighlight: string;

  // Selection
  selectedShadow: string;
  connectedShadow: string;
}

/** Layout configuration */
export interface ERDLayoutConfig {
  nodeWidth: number;
  headerHeight: number;
  columnHeight: number;
  horizontalGap: number;
  verticalGap: number;
  columnsPerRow: number;
}

/** Zoom configuration */
export interface ERDZoomConfig {
  minScale: number;
  maxScale: number;
  zoomStep: number;
}

/** Grayscale effect settings */
export interface ERDGrayscaleSettings {
  enabled: boolean;
  opacity: number; // 0-1, opacity of grayscale elements
}

/** Visual effects settings */
export interface ERDEffectsSettings {
  grayscale: ERDGrayscaleSettings;
  bridgeSize: number; // Size of line crossing bridges
}

/** ERD Settings for UI controls */
export interface ERDSettings {
  primaryColor: string;
  grayscaleEnabled: boolean;
  grayscaleOpacity: number; // 0-1, opacity of grayscale elements
}

/** Main ERD configuration */
export interface ERDConfig {
  colors: ERDColors;
  layout: ERDLayoutConfig;
  zoom: ERDZoomConfig;
  effects: ERDEffectsSettings;

  // Feature flags
  enablePanZoom: boolean;
  enableDragging: boolean;
  enableSelection: boolean;
  enableExpand: boolean;
  enableSave: boolean;
}

// ============================================================================
// Event Types
// ============================================================================

export interface ERDTableClickEvent {
  tableId: string;
  tableName: string;
}

export interface ERDSaveEvent {
  nodes: ERDNode[];
  transform: Transform;
}

export interface ERDDragEvent {
  nodeId: string;
  position: Position;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface ERDContainerProps {
  tables: Table[];
  relationships?: ERDRelationship[];
  config?: Partial<ERDConfig>;
  initialNodePositions?: Map<string, Position>;
  selectedTableId?: string;
  onTableClick?: (event: ERDTableClickEvent) => void;
  onSave?: (event: ERDSaveEvent) => void;
  onNodeDrag?: (event: ERDDragEvent) => void;
  className?: string;
  style?: React.CSSProperties;
}

