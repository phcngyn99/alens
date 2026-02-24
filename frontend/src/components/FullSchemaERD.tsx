/**
 * FullSchemaERD - DBeaver-style ERD showing tables with PK/FK columns
 *
 * This component uses the reusable ERD library for all visualization.
 * Features:
 * - Collapsed by default: shows only table name + PK columns
 * - Click to expand and see all columns
 * - Clean orthogonal relationship lines with crossing bridges
 * - Light theme with professional styling
 * - Pan and zoom functionality
 * - Table click highlighting with connected tables/relationships
 * - Draggable tables
 * - Save diagram state
 */

import type { Table } from '../types';
import { ERDContainer } from '../lib/erd';

interface FullSchemaERDProps {
  tables: Table[];
  onTableClick?: (tableName: string) => void;
}

export default function FullSchemaERD({ tables, onTableClick }: FullSchemaERDProps) {
  return (
    <ERDContainer
      tables={tables}
      onTableClick={onTableClick}
      config={{
        enablePanZoom: true,
        enableSelection: true,
        enableExpand: true,
        enableDragging: true,
        enableSave: false,
      }}
      maxHeight="600px"
    />
  );
}