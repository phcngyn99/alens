/**
 * TableERD - ERD component showing selected table and its relationships
 *
 * This component uses the reusable ERD library for visualization.
 * It shows the selected table centered with related tables positioned around it:
 * - Selected table in the center
 * - Tables referenced by the selected table (outgoing FKs) on the right
 * - Tables that reference the selected table (incoming FKs) on the left
 *
 * Features: pan/zoom, expand/collapse, orthogonal lines with crossing bridges
 */

import { useMemo } from 'react';
import type { Table, ForeignKey } from '../types';
import { ERDContainer } from '../lib/erd';
import type { Position } from '../lib/erd/types';

interface TableERDProps {
  selectedTable: Table;
  relatedTables: Table[];
  onTableClick?: (tableName: string) => void;
}

export default function TableERD({ selectedTable, relatedTables, onTableClick }: TableERDProps) {
  // Calculate custom positions for centered layout
  const { tables, initialPositions } = useMemo(() => {
    const nodeWidth = 160;
    const horizontalGap = 80;
    const verticalGap = 30;
    const centerX = 300;
    const centerY = 30;

    // Combine selectedTable with relatedTables (avoiding duplicates)
    const allTables: Table[] = [selectedTable];
    const seenNames = new Set([selectedTable.name]);
    relatedTables.forEach((t) => {
      if (!seenNames.has(t.name)) {
        allTables.push(t);
        seenNames.add(t.name);
      }
    });

    const positions = new Map<string, Position>();

    // Position the selected table in the center
    positions.set(selectedTable.name, {
      x: centerX - nodeWidth / 2,
      y: centerY,
    });

    // Identify outgoing FK relationships (tables this table references)
    const outgoingTableNames = new Set(
      selectedTable.foreign_keys.map((fk: ForeignKey) => fk.referenced_table)
    );

    // Identify incoming FK relationships (tables that reference this table)
    const incomingTableNames = new Set<string>();
    relatedTables.forEach((t) => {
      t.foreign_keys.forEach((fk: ForeignKey) => {
        if (
          fk.referenced_table === selectedTable.name &&
          fk.referenced_schema === selectedTable.schema_name
        ) {
          incomingTableNames.add(t.name);
        }
      });
    });

    // Position outgoing tables (referenced by selected) on the right
    let rightY = centerY;
    allTables.forEach((table) => {
      if (outgoingTableNames.has(table.name) && table.name !== selectedTable.name) {
        positions.set(table.name, {
          x: centerX + nodeWidth / 2 + horizontalGap,
          y: rightY,
        });
        // Estimate height for next position (will be refined by ERDContainer)
        rightY += 80 + verticalGap;
      }
    });

    // Position incoming tables (referencing selected) on the left
    let leftY = centerY;
    allTables.forEach((table) => {
      if (incomingTableNames.has(table.name) && table.name !== selectedTable.name && !positions.has(table.name)) {
        positions.set(table.name, {
          x: centerX - nodeWidth / 2 - horizontalGap - nodeWidth,
          y: leftY,
        });
        leftY += 80 + verticalGap;
      }
    });

    // Normalize positions to start from 0
    const allX = Array.from(positions.values()).map((p) => p.x);
    const minX = allX.length > 0 ? Math.min(...allX) : 0;
    if (minX < 30) {
      const offsetX = 30 - minX;
      positions.forEach((pos, key) => {
        positions.set(key, { x: pos.x + offsetX, y: pos.y });
      });
    }

    return { tables: allTables, initialPositions: positions };
  }, [selectedTable, relatedTables]);

  return (
    <ERDContainer
      tables={tables}
      initialPositions={initialPositions}
      onTableClick={onTableClick}
      config={{
        enablePanZoom: true,
        enableSelection: true,
        enableExpand: true,
        enableDragging: true,
        enableSave: false,
      }}
      maxHeight="400px"
    />
  );
}
