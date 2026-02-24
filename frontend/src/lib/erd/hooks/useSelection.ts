/**
 * Selection Hook for ERD
 * Handles table selection and highlighting logic
 */

import { useState, useCallback, useMemo } from 'react';
import type { ERDRelationship, ERDTableClickEvent } from '../types';
import { getConnectedTables, isRelationshipConnected } from '../utils';

interface UseSelectionOptions {
  enabled?: boolean;
  relationships: ERDRelationship[];
  onTableClick?: (event: ERDTableClickEvent) => void;
}

interface UseSelectionReturn {
  selectedTableId: string | null;
  connectedTableIds: Set<string>;
  isTableSelected: (tableId: string) => boolean;
  isTableConnected: (tableId: string) => boolean;
  isTableDimmed: (tableId: string) => boolean;
  isRelationshipHighlighted: (rel: ERDRelationship) => boolean;
  selectTable: (tableId: string, e?: React.MouseEvent) => void;
  clearSelection: () => void;
}

export function useSelection(options: UseSelectionOptions): UseSelectionReturn {
  const { enabled = true, relationships, onTableClick } = options;

  const [selectedTableId, setSelectedTableId] = useState<string | null>(null);

  // Get connected tables for the selected table
  const connectedTableIds = useMemo(() => {
    return getConnectedTables(selectedTableId, relationships);
  }, [selectedTableId, relationships]);

  const isTableSelected = useCallback(
    (tableId: string) => selectedTableId === tableId,
    [selectedTableId]
  );

  const isTableConnected = useCallback(
    (tableId: string) => connectedTableIds.has(tableId),
    [connectedTableIds]
  );

  const isTableDimmed = useCallback(
    (tableId: string) => {
      if (!selectedTableId) return false;
      return !isTableSelected(tableId) && !isTableConnected(tableId);
    },
    [selectedTableId, isTableSelected, isTableConnected]
  );

  const isRelationshipHighlighted = useCallback(
    (rel: ERDRelationship) => isRelationshipConnected(rel, selectedTableId),
    [selectedTableId]
  );

  const selectTable = useCallback(
    (tableId: string, e?: React.MouseEvent) => {
      if (!enabled) return;
      e?.stopPropagation();
      
      setSelectedTableId((prev) => (prev === tableId ? null : tableId));
      onTableClick?.({ tableId, tableName: tableId });
    },
    [enabled, onTableClick]
  );

  const clearSelection = useCallback(() => {
    setSelectedTableId(null);
  }, []);

  return {
    selectedTableId,
    connectedTableIds,
    isTableSelected,
    isTableConnected,
    isTableDimmed,
    isRelationshipHighlighted,
    selectTable,
    clearSelection,
  };
}

