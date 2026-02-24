/**
 * ERD Library Utility Functions
 * Reusable functions for path calculation, crossing detection, and layout
 */

import type { PathSegment, CrossingPoint, ERDNode, ERDRelationship, ERDLayoutConfig } from './types';
import type { Table } from '../../types';

// ============================================================================
// Constants
// ============================================================================

/** Default viewport dimensions for ERD canvas */
export const DEFAULT_VIEWPORT_WIDTH = 1400;
export const DEFAULT_VIEWPORT_HEIGHT = 600;

// ============================================================================
// Path Calculation
// ============================================================================

/**
 * Calculate column Y position within a node for relationship line positioning
 */
export function getColumnYPosition(
  node: ERDNode,
  columnName: string,
  isExpanded: boolean,
  headerHeight: number = 26,
  columnHeight: number = 18
): number {
  const keyColumns = getKeyColumns(node.table);
  const displayColumns = isExpanded ? node.table.columns : keyColumns;
  const columnIndex = displayColumns.findIndex((c) => c.name === columnName);

  if (columnIndex >= 0) {
    return node.y + headerHeight + columnIndex * columnHeight + columnHeight / 2 + 4;
  }
  return node.y + headerHeight + columnHeight / 2;
}

/**
 * Get path segments from two nodes for crossing detection
 */
export function getPathSegments(
  fromNode: ERDNode,
  toNode: ERDNode,
  fromColumn: string,
  toColumn: string,
  offset: number,
  isFromExpanded: boolean,
  isToExpanded: boolean,
  headerHeight: number = 26,
  columnHeight: number = 18
): PathSegment[] {
  const fromCenterX = fromNode.x + fromNode.width / 2;
  const toCenterX = toNode.x + toNode.width / 2;
  const fromY = getColumnYPosition(fromNode, fromColumn, isFromExpanded, headerHeight, columnHeight) + offset;
  const toY = getColumnYPosition(toNode, toColumn, isToExpanded, headerHeight, columnHeight) + offset;

  let x1: number, x2: number;
  if (fromCenterX < toCenterX) {
    x1 = fromNode.x + fromNode.width;
    x2 = toNode.x;
  } else {
    x1 = fromNode.x;
    x2 = toNode.x + toNode.width;
  }
  const midX = (x1 + x2) / 2;

  return [
    { x1, y1: fromY, x2: midX, y2: fromY, isVertical: false },
    { x1: midX, y1: fromY, x2: midX, y2: toY, isVertical: true },
    { x1: midX, y1: toY, x2: x2, y2: toY, isVertical: false },
  ];
}

/**
 * Check if a vertical segment crosses a horizontal segment
 */
export function findCrossing(
  vertSeg: PathSegment,
  horzSeg: PathSegment
): CrossingPoint | null {
  const vx = vertSeg.x1;
  const vy1 = Math.min(vertSeg.y1, vertSeg.y2);
  const vy2 = Math.max(vertSeg.y1, vertSeg.y2);
  const hy = horzSeg.y1;
  const hx1 = Math.min(horzSeg.x1, horzSeg.x2);
  const hx2 = Math.max(horzSeg.x1, horzSeg.x2);

  if (vx > hx1 && vx < hx2 && hy > vy1 && hy < vy2) {
    return { x: vx, y: hy };
  }
  return null;
}

/**
 * Generate SVG path with bridges (arc jumps) over crossings
 * Creates a perfect semicircular arc that jumps over the crossing line
 *
 * The bridge creates a visual "jump" effect where one line appears to go over another.
 * Uses SVG arc commands to draw perfect semicircles.
 *
 * Arc command: A rx ry x-axis-rotation large-arc-flag sweep-flag x y
 * - rx, ry: radius (same for circle)
 * - large-arc-flag: 0 for minor arc (< 180°), 1 for major arc (> 180°)
 * - sweep-flag: 0 for counter-clockwise, 1 for clockwise
 *
 * @returns Object with path string and whether bridges were drawn
 */
export function generatePathWithBridges(
  segments: PathSegment[],
  crossings: CrossingPoint[],
  bridgeSize: number = 4
): { path: string; hasBridges: boolean } {
  let path = `M ${segments[0].x1} ${segments[0].y1}`;
  let hasBridges = false;

  // Radius of the semicircle - this is the distance from the crossing point
  const r = bridgeSize;
  // Tolerance for floating-point comparison
  const tolerance = 1;

  for (const seg of segments) {
    if (seg.isVertical) {
      // Find crossings on this vertical segment
      const minY = Math.min(seg.y1, seg.y2);
      const maxY = Math.max(seg.y1, seg.y2);
      const segCrossings = crossings.filter(
        (c) => Math.abs(c.x - seg.x1) < tolerance && c.y > minY + r && c.y < maxY - r
      ).sort((a, b) => (seg.y2 > seg.y1 ? a.y - b.y : b.y - a.y));

      for (const crossing of segCrossings) {
        hasBridges = true;
        const x = seg.x1;
        const y = crossing.y;
        // Draw vertical line to r pixels before crossing
        path += ` V ${y - r}`;
        // Create semicircular arc going RIGHT then back LEFT
        // From (x, y-r) → arc right to (x+r, y) → arc back left to (x, y+r)
        // Using two quadratic curves to create smooth semicircle (consistent with horizontal)
        path += ` Q ${x + r} ${y - r}, ${x + r} ${y}`;  // Right-down quarter
        path += ` Q ${x + r} ${y + r}, ${x} ${y + r}`;  // Left-down quarter
      }
      path += ` V ${seg.y2}`;
    } else {
      // Horizontal segment - check for crossings with vertical lines
      const minX = Math.min(seg.x1, seg.x2);
      const maxX = Math.max(seg.x1, seg.x2);
      const segCrossings = crossings.filter(
        (c) => Math.abs(c.y - seg.y1) < tolerance && c.x > minX + r && c.x < maxX - r
      ).sort((a, b) => (seg.x2 > seg.x1 ? a.x - b.x : b.x - a.x));

      for (const crossing of segCrossings) {
        hasBridges = true;
        const x = crossing.x;
        const y = seg.y1;
        // Draw horizontal line to r pixels before crossing
        path += ` H ${x - r}`;
        // Create semicircular arc going DOWN then back UP
        // From (x-r, y) → arc down to (x, y+r) → arc back up to (x+r, y)
        // Using two quadratic curves to create smooth semicircle
        path += ` Q ${x - r} ${y + r}, ${x} ${y + r}`;  // Down-right quarter
        path += ` Q ${x + r} ${y + r}, ${x + r} ${y}`;  // Up-right quarter
      }
      path += ` H ${seg.x2}`;
    }
  }
  return { path, hasBridges };
}

/**
 * Generate simple orthogonal path without bridges
 */
export function generateSimplePath(
  x1: number, y1: number, x2: number, y2: number
): string {
  const midX = (x1 + x2) / 2;
  return `M ${x1} ${y1} H ${midX} V ${y2} H ${x2}`;
}

// ============================================================================
// Table Helpers
// ============================================================================

/**
 * Get only primary key columns for collapsed view
 */
export function getKeyColumns(table: Table) {
  return table.columns.filter((c) => c.is_primary_key);
}

/**
 * Calculate node height based on displayed columns
 */
export function calculateNodeHeight(
  table: Table,
  isExpanded: boolean,
  headerHeight: number = 26,
  columnHeight: number = 18
): number {
  const keyColumns = getKeyColumns(table);
  const displayColumns = isExpanded ? table.columns : keyColumns;
  const hasMore = !isExpanded && table.columns.length > keyColumns.length;
  return headerHeight + displayColumns.length * columnHeight + (hasMore ? columnHeight : 0) + 8;
}

// ============================================================================
// Layout Calculation
// ============================================================================

/**
 * Extract relationships from tables' foreign keys
 */
export function extractRelationships(tables: Table[]): ERDRelationship[] {
  const relationships: ERDRelationship[] = [];
  tables.forEach((table) => {
    table.foreign_keys.forEach((fk) => {
      fk.columns.forEach((col, idx) => {
        relationships.push({
          id: `${table.name}-${fk.referenced_table}-${col}`,
          fromTable: table.name,
          fromColumn: col,
          toTable: fk.referenced_table,
          toColumn: fk.referenced_columns[idx] || fk.referenced_columns[0],
          foreignKey: fk,
        });
      });
    });
  });
  return relationships;
}

/**
 * Build adjacency map for layout optimization
 */
export function buildAdjacencyMap(
  tables: Table[],
  relationships: ERDRelationship[]
): Map<string, Set<string>> {
  const adjacency = new Map<string, Set<string>>();
  tables.forEach((t) => adjacency.set(t.name, new Set()));
  relationships.forEach((r) => {
    adjacency.get(r.fromTable)?.add(r.toTable);
    adjacency.get(r.toTable)?.add(r.fromTable);
  });
  return adjacency;
}

/**
 * Sort tables by connectivity (most connected first)
 */
export function sortTablesByConnectivity(
  tables: Table[],
  adjacency: Map<string, Set<string>>
): Table[] {
  return [...tables].sort((a, b) => {
    const aConns = adjacency.get(a.name)?.size || 0;
    const bConns = adjacency.get(b.name)?.size || 0;
    if (bConns !== aConns) return bConns - aConns;
    return a.name.localeCompare(b.name);
  });
}

/**
 * Calculate grid layout positions for nodes
 * Places the most connected table (first in sorted array) in the center
 * and centers the entire group of tables in the view
 */
export function calculateGridLayout(
  tables: Table[],
  expandedTables: Set<string>,
  config: ERDLayoutConfig
): { nodes: ERDNode[]; svgWidth: number; svgHeight: number } {
  const { nodeWidth, headerHeight, columnHeight, horizontalGap, verticalGap, columnsPerRow } = config;

  if (tables.length === 0) {
    return { nodes: [], svgWidth: 400, svgHeight: 300 };
  }

  const cols = columnsPerRow > 0 ? columnsPerRow : Math.max(2, Math.ceil(Math.sqrt(tables.length)));

  // First pass: Calculate positions in a standard grid starting from (0, 0)
  const tempNodes: ERDNode[] = tables.map((table, idx) => {
    const isExpanded = expandedTables.has(table.name);
    const height = calculateNodeHeight(table, isExpanded, headerHeight, columnHeight);

    const col = idx % cols;
    const row = Math.floor(idx / cols);

    return {
      id: table.name,
      table,
      x: col * (nodeWidth + horizontalGap),
      y: row * (120 + verticalGap),
      width: nodeWidth,
      height,
    };
  });

  // Calculate the bounding box of all nodes
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  tempNodes.forEach((node) => {
    minX = Math.min(minX, node.x);
    minY = Math.min(minY, node.y);
    maxX = Math.max(maxX, node.x + node.width);
    maxY = Math.max(maxY, node.y + node.height);
  });

  // Calculate the size of the content
  const contentWidth = maxX - minX;
  const contentHeight = maxY - minY;

  // Calculate offset to center the content in the viewport
  const offsetX = (DEFAULT_VIEWPORT_WIDTH - contentWidth) / 2;
  const offsetY = (DEFAULT_VIEWPORT_HEIGHT - contentHeight) / 2;

  // Apply offset to all nodes to center the group
  const nodes: ERDNode[] = tempNodes.map((node) => ({
    ...node,
    x: node.x + offsetX,
    y: node.y + offsetY,
  }));

  return {
    nodes,
    svgWidth: DEFAULT_VIEWPORT_WIDTH,
    svgHeight: DEFAULT_VIEWPORT_HEIGHT,
  };
}

/**
 * Group relationships by table pairs for offset calculation
 */
export function groupRelationshipsByPair(
  relationships: ERDRelationship[]
): Map<string, { offset: number; total: number }> {
  const pairCounts = new Map<string, number>();
  const pairIndices = new Map<string, number>();

  relationships.forEach((rel) => {
    const key = [rel.fromTable, rel.toTable].sort().join('|');
    pairCounts.set(key, (pairCounts.get(key) || 0) + 1);
  });

  const result = new Map<string, { offset: number; total: number }>();
  relationships.forEach((rel, idx) => {
    const key = [rel.fromTable, rel.toTable].sort().join('|');
    const total = pairCounts.get(key) || 1;
    const currentIndex = pairIndices.get(key) || 0;
    pairIndices.set(key, currentIndex + 1);

    const relKey = `${rel.fromTable}-${rel.toTable}-${rel.fromColumn}-${idx}`;
    const offset = total > 1 ? (currentIndex - (total - 1) / 2) * 8 : 0;
    result.set(relKey, { offset, total });
  });

  return result;
}

/**
 * Get connected tables for a selected table
 */
export function getConnectedTables(
  selectedTableId: string | null,
  relationships: ERDRelationship[]
): Set<string> {
  if (!selectedTableId) return new Set<string>();

  const connected = new Set<string>();
  relationships.forEach((rel) => {
    if (rel.fromTable === selectedTableId) {
      connected.add(rel.toTable);
    } else if (rel.toTable === selectedTableId) {
      connected.add(rel.fromTable);
    }
  });
  return connected;
}

/**
 * Check if a relationship is connected to the selected table
 */
export function isRelationshipConnected(
  rel: ERDRelationship,
  selectedTableId: string | null
): boolean {
  if (!selectedTableId) return false;
  return rel.fromTable === selectedTableId || rel.toTable === selectedTableId;
}

