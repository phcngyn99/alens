/**
 * Drag Hook for ERD Nodes
 * Handles drag interactions for moveable table nodes with collision detection
 */

import { useState, useCallback, useRef } from 'react';
import type { Position, ERDNode, ERDDragEvent } from '../types';

interface UseDragOptions {
  enabled?: boolean;
  onDrag?: (event: ERDDragEvent) => void;
  onDragEnd?: (event: ERDDragEvent) => void;
  collisionPadding?: number; // Minimum gap between nodes
}

interface NodeBounds {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface UseDragReturn {
  dragState: {
    isDragging: boolean;
    nodeId: string | null;
    startPosition: Position | null;
    currentOffset: Position;
  };
  getDragOffset: (nodeId: string) => Position;
  handlers: {
    onNodeMouseDown: (nodeId: string, e: React.MouseEvent) => void;
    onMouseMove: (e: React.MouseEvent) => void;
    onMouseUp: () => void;
  };
  nodePositions: Map<string, Position>;
  updateNodePosition: (nodeId: string, position: Position) => void;
  resetPositions: () => void;
  setNodeBounds: (bounds: NodeBounds[]) => void;
}

/**
 * Check if two rectangles overlap
 */
function checkCollision(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
  padding: number
): boolean {
  return !(
    a.x + a.width + padding <= b.x ||
    b.x + b.width + padding <= a.x ||
    a.y + a.height + padding <= b.y ||
    b.y + b.height + padding <= a.y
  );
}

/**
 * Find a non-overlapping position for a node
 */
function findNonOverlappingPosition(
  nodeId: string,
  targetPos: Position,
  nodeBounds: NodeBounds[],
  padding: number
): Position {
  const currentNode = nodeBounds.find((n) => n.id === nodeId);
  if (!currentNode) return targetPos;

  const movingNode = {
    ...currentNode,
    x: targetPos.x,
    y: targetPos.y,
  };

  // Check for collisions with other nodes
  let hasCollision = false;
  for (const other of nodeBounds) {
    if (other.id === nodeId) continue;
    if (checkCollision(movingNode, other, padding)) {
      hasCollision = true;
      break;
    }
  }

  if (!hasCollision) return targetPos;

  // Find the nearest non-overlapping position
  // Try adjusting in different directions
  const directions = [
    { dx: 1, dy: 0 },   // right
    { dx: -1, dy: 0 },  // left
    { dx: 0, dy: 1 },   // down
    { dx: 0, dy: -1 },  // up
    { dx: 1, dy: 1 },   // diagonal
    { dx: -1, dy: 1 },
    { dx: 1, dy: -1 },
    { dx: -1, dy: -1 },
  ];

  const step = 10;
  const maxIterations = 50;

  for (let i = 1; i <= maxIterations; i++) {
    for (const dir of directions) {
      const testPos = {
        x: targetPos.x + dir.dx * step * i,
        y: Math.max(0, targetPos.y + dir.dy * step * i), // Don't go above 0
      };
      const testNode = { ...movingNode, x: testPos.x, y: testPos.y };

      let collides = false;
      for (const other of nodeBounds) {
        if (other.id === nodeId) continue;
        if (checkCollision(testNode, other, padding)) {
          collides = true;
          break;
        }
      }

      if (!collides) {
        return testPos;
      }
    }
  }

  // If no position found, return original target (shouldn't happen often)
  return targetPos;
}

export function useDrag(
  initialNodes: ERDNode[],
  options: UseDragOptions = {}
): UseDragReturn {
  const { enabled = true, onDrag, onDragEnd, collisionPadding = 10 } = options;

  // Store custom node positions (overrides from dragging)
  const [nodePositions, setNodePositions] = useState<Map<string, Position>>(
    () => new Map(initialNodes.map((n) => [n.id, { x: n.x, y: n.y }]))
  );

  // Store node bounds for collision detection
  const nodeBoundsRef = useRef<NodeBounds[]>(
    initialNodes.map((n) => ({ id: n.id, x: n.x, y: n.y, width: n.width, height: n.height }))
  );

  const [isDragging, setIsDragging] = useState(false);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [startPosition, setStartPosition] = useState<Position | null>(null);
  const [currentOffset, setCurrentOffset] = useState<Position>({ x: 0, y: 0 });

  const setNodeBounds = useCallback((bounds: NodeBounds[]) => {
    nodeBoundsRef.current = bounds;
  }, []);

  const onNodeMouseDown = useCallback((nodeId: string, e: React.MouseEvent) => {
    if (!enabled) return;
    e.stopPropagation();

    const currentPos = nodePositions.get(nodeId) || { x: 0, y: 0 };
    setIsDragging(true);
    setDraggingNodeId(nodeId);
    setStartPosition({ x: e.clientX - currentPos.x, y: e.clientY - currentPos.y });
    setCurrentOffset({ x: 0, y: 0 });
  }, [enabled, nodePositions]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!enabled || !isDragging || !draggingNodeId || !startPosition) return;

    const newX = e.clientX - startPosition.x;
    const newY = Math.max(0, e.clientY - startPosition.y); // Don't go above 0
    const rawPosition = { x: newX, y: newY };

    // Apply collision detection
    const adjustedPosition = findNonOverlappingPosition(
      draggingNodeId,
      rawPosition,
      nodeBoundsRef.current,
      collisionPadding
    );

    setNodePositions((prev) => {
      const updated = new Map(prev);
      updated.set(draggingNodeId, adjustedPosition);
      return updated;
    });

    // Update bounds for the dragging node
    nodeBoundsRef.current = nodeBoundsRef.current.map((b) =>
      b.id === draggingNodeId ? { ...b, x: adjustedPosition.x, y: adjustedPosition.y } : b
    );

    setCurrentOffset({
      x: adjustedPosition.x - (nodePositions.get(draggingNodeId)?.x || 0),
      y: adjustedPosition.y - (nodePositions.get(draggingNodeId)?.y || 0),
    });

    onDrag?.({ nodeId: draggingNodeId, position: adjustedPosition });
  }, [enabled, isDragging, draggingNodeId, startPosition, nodePositions, onDrag, collisionPadding]);

  const onMouseUp = useCallback(() => {
    if (isDragging && draggingNodeId) {
      const finalPosition = nodePositions.get(draggingNodeId);
      if (finalPosition) {
        onDragEnd?.({ nodeId: draggingNodeId, position: finalPosition });
      }
    }
    setIsDragging(false);
    setDraggingNodeId(null);
    setStartPosition(null);
    setCurrentOffset({ x: 0, y: 0 });
  }, [isDragging, draggingNodeId, nodePositions, onDragEnd]);

  const getDragOffset = useCallback((nodeId: string): Position => {
    if (isDragging && nodeId === draggingNodeId) {
      return currentOffset;
    }
    return { x: 0, y: 0 };
  }, [isDragging, draggingNodeId, currentOffset]);

  const updateNodePosition = useCallback((nodeId: string, position: Position) => {
    setNodePositions((prev) => {
      const updated = new Map(prev);
      updated.set(nodeId, position);
      return updated;
    });
  }, []);

  const resetPositions = useCallback(() => {
    setNodePositions(new Map(initialNodes.map((n) => [n.id, { x: n.x, y: n.y }])));
    nodeBoundsRef.current = initialNodes.map((n) => ({
      id: n.id, x: n.x, y: n.y, width: n.width, height: n.height
    }));
  }, [initialNodes]);

  return {
    dragState: {
      isDragging,
      nodeId: draggingNodeId,
      startPosition,
      currentOffset,
    },
    getDragOffset,
    handlers: {
      onNodeMouseDown,
      onMouseMove,
      onMouseUp,
    },
    nodePositions,
    updateNodePosition,
    resetPositions,
    setNodeBounds,
  };
}

