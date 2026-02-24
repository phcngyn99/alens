/**
 * ERDContainer Component
 * Main container component that orchestrates the ERD diagram
 */

import { useState, useMemo, useCallback, useEffect } from 'react';
import type { Table } from '../../../types';
import type { ERDConfig, ERDRelationship, Position, ERDSaveEvent } from '../types';
import { mergeConfig } from '../config';
import { usePanZoom, useDrag, useSelection } from '../hooks';
import { useERDSettings } from '../contexts';
import {
  extractRelationships,
  buildAdjacencyMap,
  sortTablesByConnectivity,
  calculateGridLayout,
  groupRelationshipsByPair,
  getPathSegments,
  findCrossing,
  generatePathWithBridges,
  getColumnYPosition,
  getKeyColumns,
} from '../utils';
import type { PathSegment, CrossingPoint } from '../types';
import { ERDTable } from './ERDTable';
import { ERDRelationship as ERDRelationshipLine } from './ERDRelationship';
import { ERDControls } from './ERDControls';
import { ERDMarkers } from './ERDMarkers';

interface ERDContainerProps {
  tables: Table[];
  config?: Partial<ERDConfig>;
  initialPositions?: Map<string, Position>;
  onTableClick?: (tableName: string) => void;
  onSave?: (event: ERDSaveEvent) => void;
  className?: string;
  style?: React.CSSProperties;
  maxHeight?: string;
}

/**
 * ERD Container component that uses the settings context
 */
export function ERDContainer({
  tables,
  config: partialConfig,
  initialPositions,
  onTableClick,
  onSave,
  className = '',
  style,
  maxHeight = '600px',
}: ERDContainerProps) {
  const [config] = useState(() => mergeConfig(partialConfig));
  const { colors, layout, zoom } = config;

  // Get settings from context
  const { settings } = useERDSettings();

  // Update config when partialConfig changes
  useEffect(() => {
    // Config updates are now handled through the settings context
  }, [partialConfig]);

  // Expand state for tables
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());

  const toggleExpand = useCallback((tableName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) next.delete(tableName);
      else next.add(tableName);
      return next;
    });
  }, []);

  // Extract relationships and calculate layout
  const relationships = useMemo(() => extractRelationships(tables), [tables]);
  const adjacency = useMemo(() => buildAdjacencyMap(tables, relationships), [tables, relationships]);
  const sortedTables = useMemo(() => sortTablesByConnectivity(tables, adjacency), [tables, adjacency]);

  const { nodes: initialNodes, svgWidth, svgHeight } = useMemo(
    () => calculateGridLayout(sortedTables, expandedTables, layout),
    [sortedTables, expandedTables, layout]
  );

  // Calculate initial transform to center the view on the most connected table
  const initialTransform = useMemo(() => {
    if (initialNodes.length === 0) {
      return { x: 0, y: 0, scale: 1 };
    }

    // The most connected table is already centered in the SVG canvas
    // We just need to ensure the view starts centered (no additional transform needed)
    return { x: 0, y: 0, scale: 1 };
  }, [initialNodes]);

  // Hooks
  const { transform, isPanning, handlers: panHandlers, controls, zoomPercentage } = usePanZoom({
    enabled: config.enablePanZoom,
    zoomConfig: zoom,
    initialTransform,
  });

  const { nodePositions, handlers: dragHandlers, setNodeBounds } = useDrag(initialNodes, {
    enabled: config.enableDragging,
    collisionPadding: 10,
  });

  const { selectedTableId, isTableSelected, isTableConnected, isTableDimmed, isRelationshipHighlighted, selectTable, clearSelection } = useSelection({
    enabled: config.enableSelection,
    relationships,
    onTableClick: (e) => onTableClick?.(e.tableName),
  });

  // Apply custom positions to nodes
  // Priority: nodePositions (active drag) > initialPositions (saved) > initialNodes (default)
  const nodes = useMemo(() => {
    const result = initialNodes.map((node) => {
      // First check nodePositions (active drag positions), then fall back to initialPositions
      const customPos = nodePositions.get(node.id) || initialPositions?.get(node.id);
      if (customPos) {
        return { ...node, x: customPos.x, y: customPos.y };
      }
      return node;
    });
    return result;
  }, [initialNodes, initialPositions, nodePositions]);

  // Update node bounds for collision detection when nodes or expanded state changes
  useEffect(() => {
    if (config.enableDragging) {
      const expandButtonHeight = 20;
      const bounds = nodes.map((node) => {
        const isExpanded = expandedTables.has(node.id);
        const keyColumns = getKeyColumns(node.table);
        const displayColumns = isExpanded ? node.table.columns : keyColumns;
        const hasMore = !isExpanded && node.table.columns.length > keyColumns.length;
        const height = layout.headerHeight + displayColumns.length * layout.columnHeight +
          (hasMore || isExpanded ? expandButtonHeight : 0) + 4;

        return {
          id: node.id,
          x: node.x,
          y: node.y,
          width: node.width,
          height: height,
        };
      });
      setNodeBounds(bounds);
    }
  }, [nodes, expandedTables, config.enableDragging, layout.headerHeight, layout.columnHeight, setNodeBounds]);

  // Calculate connection offsets for parallel lines
  const connectionOffsets = useMemo(() => groupRelationshipsByPair(relationships), [relationships]);

  // Calculate all path segments for crossing detection
  const allPathSegments = useMemo(() => {
    const segments: { relIdx: number; segments: PathSegment[] }[] = [];
    relationships.forEach((rel, idx) => {
      const fromNode = nodes.find((n) => n.id === rel.fromTable);
      const toNode = nodes.find((n) => n.id === rel.toTable);
      if (!fromNode || !toNode || fromNode === toNode) return;

      const relKey = `${rel.fromTable}-${rel.toTable}-${rel.fromColumn}-${idx}`;
      const offsetInfo = connectionOffsets.get(relKey);
      const offset = offsetInfo?.offset || 0;

      const isFromExpanded = expandedTables.has(fromNode.id);
      const isToExpanded = expandedTables.has(toNode.id);

      const pathSegs = getPathSegments(
        fromNode, toNode, rel.fromColumn, rel.toColumn, offset,
        isFromExpanded, isToExpanded, layout.headerHeight, layout.columnHeight
      );
      segments.push({ relIdx: idx, segments: pathSegs });
    });
    return segments;
  }, [relationships, nodes, connectionOffsets, expandedTables, layout]);

  // Find all crossings between different paths
  // IMPORTANT: Only HORIZONTAL lines get the jump effect (they go OVER vertical lines)
  // Vertical lines stay straight (they go BEHIND horizontal lines)
  // The line with jump effect is rendered ON TOP of the straight line
  const pathCrossings = useMemo(() => {
    const crossingsMap = new Map<number, CrossingPoint[]>();

    // Initialize empty arrays for all paths
    for (const path of allPathSegments) {
      crossingsMap.set(path.relIdx, []);
    }

    // Compare each pair of paths
    for (let i = 0; i < allPathSegments.length; i++) {
      const pathA = allPathSegments[i];

      for (let j = i + 1; j < allPathSegments.length; j++) {
        const pathB = allPathSegments[j];

        // Find crossings: vertical segment of pathA crossing horizontal segment of pathB
        // The HORIZONTAL segment (pathB) gets the crossing - it goes OVER
        for (const segA of pathA.segments) {
          if (!segA.isVertical) continue;
          for (const segB of pathB.segments) {
            if (segB.isVertical) continue;
            const crossing = findCrossing(segA, segB);
            if (crossing) {
              // Horizontal line (pathB) gets the jump - it goes OVER the vertical line
              const horizontalCrossings = crossingsMap.get(pathB.relIdx) || [];
              if (!horizontalCrossings.some(c =>
                Math.abs(c.x - crossing.x) < 1 && Math.abs(c.y - crossing.y) < 1
              )) {
                horizontalCrossings.push(crossing);
                crossingsMap.set(pathB.relIdx, horizontalCrossings);
              }
            }
          }
        }

        // Find crossings: horizontal segment of pathA crossing vertical segment of pathB
        // The HORIZONTAL segment (pathA) gets the crossing - it goes OVER
        for (const segA of pathA.segments) {
          if (segA.isVertical) continue;
          for (const segB of pathB.segments) {
            if (!segB.isVertical) continue;
            const crossing = findCrossing(segB, segA);
            if (crossing) {
              // Horizontal line (pathA) gets the jump - it goes OVER the vertical line
              const horizontalCrossings = crossingsMap.get(pathA.relIdx) || [];
              if (!horizontalCrossings.some(c =>
                Math.abs(c.x - crossing.x) < 1 && Math.abs(c.y - crossing.y) < 1
              )) {
                horizontalCrossings.push(crossing);
                crossingsMap.set(pathA.relIdx, horizontalCrossings);
              }
            }
          }
        }
      }
    }
    return crossingsMap;
  }, [allPathSegments]);

  /**
   * Generate path data for a relationship with bridge arcs at crossings
   * Returns path string and cardinality label positions
   */
  const getPathData = useCallback((rel: ERDRelationship, idx: number): {
    path: string;
    fromLabelPos: { x: number; y: number };
    toLabelPos: { x: number; y: number };
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  } | null => {
    const fromNode = nodes.find((n) => n.id === rel.fromTable);
    const toNode = nodes.find((n) => n.id === rel.toTable);
    if (!fromNode || !toNode || fromNode === toNode) return null;

    const relKey = `${rel.fromTable}-${rel.toTable}-${rel.fromColumn}-${idx}`;
    const offsetInfo = connectionOffsets.get(relKey);
    const offset = offsetInfo?.offset || 0;

    const isFromExpanded = expandedTables.has(fromNode.id);
    const isToExpanded = expandedTables.has(toNode.id);

    const fromY = getColumnYPosition(fromNode, rel.fromColumn, isFromExpanded, layout.headerHeight, layout.columnHeight) + offset;
    const toY = getColumnYPosition(toNode, rel.toColumn, isToExpanded, layout.headerHeight, layout.columnHeight) + offset;
    const fromCenterX = fromNode.x + fromNode.width / 2;
    const toCenterX = toNode.x + toNode.width / 2;
    const x1 = fromCenterX < toCenterX ? fromNode.x + fromNode.width : fromNode.x;
    const x2 = fromCenterX < toCenterX ? toNode.x : toNode.x + toNode.width;

    // Get path segments and crossings for this relationship
    const pathSegmentData = allPathSegments.find((p) => p.relIdx === idx);
    const crossings = pathCrossings.get(idx) || [];

    // Generate path with bridge arcs at crossings
    let path: string;
    if (pathSegmentData && crossings.length > 0) {
      const result = generatePathWithBridges(pathSegmentData.segments, crossings, 6);
      path = result.path;
    } else if (pathSegmentData) {
      // No crossings, generate simple path from segments
      const segs = pathSegmentData.segments;
      path = `M ${segs[0].x1} ${segs[0].y1} H ${segs[0].x2} V ${segs[1].y2} H ${segs[2].x2}`;
    } else {
      // Fallback
      const midX = (x1 + x2) / 2;
      path = `M ${x1} ${fromY} H ${midX} V ${toY} H ${x2}`;
    }

    // Calculate label positions (offset from endpoints)
    const labelOffset = 12;
    const fromLabelPos = {
      x: fromCenterX < toCenterX ? x1 + labelOffset : x1 - labelOffset,
      y: fromY - 8,
    };
    const toLabelPos = {
      x: fromCenterX < toCenterX ? x2 - labelOffset : x2 + labelOffset,
      y: toY - 8,
    };

    return {
      path,
      fromLabelPos,
      toLabelPos,
      x1,
      y1: fromY,
      x2,
      y2: toY,
    };
  }, [nodes, connectionOffsets, expandedTables, layout, allPathSegments, pathCrossings]);

  // Handle save
  const handleSave = useCallback(() => {
    if (!onSave) return;
    onSave({ nodes, transform });
  }, [onSave, nodes, transform]);

  // Empty state
  if (tables.length === 0) {
    return (
      <div
        className={`border rounded-lg p-8 text-center ${className}`}
        style={{ backgroundColor: colors.containerBg, borderColor: colors.containerBorder, color: colors.regularColumnText, ...style }}
      >
        No tables to display
      </div>
    );
  }

  return (
    <div
      className={`border rounded-lg overflow-hidden relative ${className}`}
      style={{ backgroundColor: colors.containerBg, borderColor: colors.containerBorder, maxHeight, ...style }}
    >
      {/* Controls */}
      {config.enablePanZoom && (
        <ERDControls
          zoomPercentage={zoomPercentage}
          onZoomIn={controls.zoomIn}
          onZoomOut={controls.zoomOut}
          onResetView={controls.resetView}
          showSaveButton={config.enableSave}
          onSave={handleSave}
        />
      )}

      {/* SVG container */}
      <div
        className="overflow-auto w-full"
        style={{ maxHeight, cursor: isPanning ? 'grabbing' : 'grab' }}
        onMouseDown={panHandlers.onMouseDown}
        onMouseMove={(e) => {
          panHandlers.onMouseMove(e);
          if (config.enableDragging) dragHandlers.onMouseMove(e);
        }}
        onMouseUp={() => {
          panHandlers.onMouseUp();
          if (config.enableDragging) dragHandlers.onMouseUp();
        }}
        onMouseLeave={panHandlers.onMouseLeave}
        onWheel={panHandlers.onWheel}
      >
        <svg
          width={svgWidth * transform.scale}
          height={svgHeight * transform.scale}
          style={{ transform: `translate(${transform.x}px, ${transform.y}px)`, transformOrigin: '0 0' }}
        >
          <g transform={`scale(${transform.scale})`}>
            {/* Background for click handling */}
            <rect
              className="erd-background"
              x="0" y="0"
              width={svgWidth}
              height={svgHeight}
              fill={colors.containerBg}
              onClick={clearSelection}
            />

            {/* Markers */}
            <ERDMarkers colors={colors} grayscaleOpacity={settings.grayscaleOpacity} />

            {/* Relationship lines - DBeaver style with cardinality labels */}
            {/* Render in two passes: straight lines first (behind), then lines with jump effect (on top) */}

            {/* First pass: Render straight lines (lines WITHOUT jump effect - they go behind) */}
            {relationships.map((rel, idx) => {
              const crossings = pathCrossings.get(idx) || [];
              if (crossings.length > 0) return null; // Skip lines with jump effect in first pass

              const pathData = getPathData(rel, idx);
              if (!pathData) return null;
              const relKey = `${rel.fromTable}-${rel.toTable}-${rel.fromColumn}-${idx}`;
              const isHighlighted = isRelationshipHighlighted(rel);
              return (
                <g key={relKey}>
                  <ERDRelationshipLine
                    path={pathData.path}
                    colors={colors}
                    isHighlighted={isHighlighted}
                    isSelected={!!selectedTableId}
                    grayscaleEnabled={settings.grayscaleEnabled}
                    fromCardinality="1"
                    toCardinality="1..n"
                    fromLabelPos={isHighlighted ? pathData.fromLabelPos : undefined}
                    toLabelPos={isHighlighted ? pathData.toLabelPos : undefined}
                  />
                </g>
              );
            })}

            {/* Second pass: Render lines with jump effect (they go on top) */}
            {relationships.map((rel, idx) => {
              const crossings = pathCrossings.get(idx) || [];
              if (crossings.length === 0) return null; // Skip straight lines in second pass

              const pathData = getPathData(rel, idx);
              if (!pathData) return null;
              const relKey = `${rel.fromTable}-${rel.toTable}-${rel.fromColumn}-${idx}-jump`;
              const isHighlighted = isRelationshipHighlighted(rel);
              return (
                <g key={relKey}>
                  <ERDRelationshipLine
                    path={pathData.path}
                    colors={colors}
                    isHighlighted={isHighlighted}
                    isSelected={!!selectedTableId}
                    grayscaleEnabled={settings.grayscaleEnabled}
                    fromCardinality="1"
                    toCardinality="1..n"
                    fromLabelPos={isHighlighted ? pathData.fromLabelPos : undefined}
                    toLabelPos={isHighlighted ? pathData.toLabelPos : undefined}
                  />
                </g>
              );
            })}

            {/* Table nodes */}
            {nodes.map((node) => (
              <ERDTable
                key={node.id}
                node={node}
                colors={colors}
                headerHeight={layout.headerHeight}
                columnHeight={layout.columnHeight}
                isExpanded={expandedTables.has(node.id)}
                isSelected={isTableSelected(node.id)}
                isConnected={isTableConnected(node.id)}
                isDimmed={isTableDimmed(node.id)}
                grayscaleEnabled={settings.grayscaleEnabled}
                enableExpand={config.enableExpand}
                enableDrag={config.enableDragging}
                onToggleExpand={toggleExpand}
                onSelect={selectTable}
                onDragStart={config.enableDragging ? dragHandlers.onNodeMouseDown : undefined}
              />
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}

