/**
 * ERDTable Component
 * Renders a single table node in the ERD diagram - DBeaver style
 *
 * Design: Clean table cards with type indicators (123, A-Z) like DBeaver
 */

import { ChevronDown, ChevronUp } from 'lucide-react';
import type { ERDNode, ERDColors } from '../types';
import { getKeyColumns } from '../utils';

interface ERDTableProps {
  node: ERDNode;
  colors: ERDColors;
  headerHeight?: number;
  columnHeight?: number;
  isExpanded: boolean;
  isSelected: boolean;
  isConnected: boolean;
  isDimmed: boolean;
  grayscaleEnabled: boolean; // Whether grayscale effect is enabled
  enableExpand?: boolean;
  enableDrag?: boolean;
  showGridLines?: boolean;
  onToggleExpand: (tableName: string, e: React.MouseEvent) => void;
  onSelect: (tableName: string, e: React.MouseEvent) => void;
  onDragStart?: (nodeId: string, e: React.MouseEvent) => void;
}

/**
 * Get type indicator for a column based on data type - DBeaver style
 * Returns: "123" for numeric, "A-Z" for text, "📅" for dates, etc.
 */
function getTypeIndicator(dataType?: string): string {
  if (!dataType) return 'A-Z';
  const t = dataType.toLowerCase();
  if (t.includes('int') || t.includes('numeric') || t.includes('decimal') || t.includes('float') || t.includes('double') || t.includes('money') || t.includes('bit')) {
    return '123';
  }
  if (t.includes('date') || t.includes('time')) {
    return '📅';
  }
  if (t.includes('bool')) {
    return '☑';
  }
  if (t.includes('binary') || t.includes('blob') || t.includes('image')) {
    return '▣';
  }
  return 'A-Z';
}

export function ERDTable({
  node,
  colors,
  headerHeight = 26,
  columnHeight = 18,
  isExpanded,
  isSelected,
  isConnected,
  isDimmed,
  grayscaleEnabled,
  enableExpand = true,
  enableDrag = false,
  showGridLines = true,
  onToggleExpand,
  onSelect,
  onDragStart,
}: ERDTableProps) {
  const keyColumns = getKeyColumns(node.table);
  const displayColumns = isExpanded ? node.table.columns : keyColumns;
  const hasMore = !isExpanded && node.table.columns.length > keyColumns.length;
  const expandButtonHeight = hasMore || isExpanded ? 18 : 0;
  const nodeHeight = headerHeight + displayColumns.length * columnHeight + expandButtonHeight + 2;

  const handleHeaderClick = (e: React.MouseEvent) => {
    onSelect(node.table.name, e);
  };

  const handleDragStart = (e: React.MouseEvent) => {
    if (enableDrag && onDragStart) {
      onDragStart(node.id, e);
    }
  };

  // DBeaver style: primary key row gets green left border, not full bg highlight
  const getBorderColor = () => {
    if (isSelected) return colors.tableSelectedBorder;
    if (isConnected) return colors.tableConnectedBorder;
    return colors.tableBorder;
  };

  return (
    <g
      style={{
        cursor: enableDrag ? 'move' : 'default',
      }}
      filter={grayscaleEnabled && isDimmed ? 'url(#grayscale)' : undefined}
    >
      {/* Table background - simple rectangle */}
      <rect
        x={node.x}
        y={node.y}
        width={node.width}
        height={nodeHeight}
        fill={colors.tableBg}
        stroke={getBorderColor()}
        strokeWidth={isSelected ? 2 : 1}
        rx="2"
        filter={isSelected ? 'url(#selected-glow)' : undefined}
      />

      {/* Header background - DBeaver style blue header */}
      <rect
        x={node.x + 1}
        y={node.y + 1}
        width={node.width - 2}
        height={headerHeight - 2}
        fill={isSelected ? colors.tableSelectedHeaderBg : colors.tableHeaderBg}
        rx="1"
      />

      {/* Table icon and name */}
      <text
        x={node.x + 6}
        y={node.y + 16}
        fontSize="10"
        fontWeight="500"
        fill={isSelected ? colors.tableSelectedNameText : colors.tableNameText}
      >
        ⊞ {node.table.name.length > 18 ? node.table.name.slice(0, 16) + '..' : node.table.name}
      </text>

      {/* Columns */}
      {displayColumns.map((col, cidx) => {
        const y = node.y + headerHeight + cidx * columnHeight;
        const isPK = col.is_primary_key;
        const isFK = col.is_foreign_key;
        const typeIndicator = getTypeIndicator(col.data_type);

        return (
          <g key={col.name}>
            {/* Primary key indicator - green left border like DBeaver */}
            {isPK && (
              <rect
                x={node.x + 1}
                y={y}
                width={3}
                height={columnHeight}
                fill={colors.pkRowBg}
              />
            )}
            {/* Foreign key indicator - cyan left border */}
            {isFK && !isPK && (
              <rect
                x={node.x + 1}
                y={y}
                width={3}
                height={columnHeight}
                fill={colors.fkText}
              />
            )}
            {/* Grid line */}
            {showGridLines && cidx > 0 && (
              <line
                x1={node.x + 1}
                y1={y}
                x2={node.x + node.width - 1}
                y2={y}
                stroke={colors.tableBorder}
                strokeWidth={0.5}
                strokeOpacity={0.3}
              />
            )}
            {/* Type indicator (123, A-Z) */}
            <text
              x={node.x + 8}
              y={y + 13}
              fontSize="8"
              fill={isPK ? colors.pkText : isFK ? colors.fkText : colors.regularColumnText}
              fontFamily="monospace"
            >
              {typeIndicator}
            </text>
            {/* Column name - bold if PK */}
            <text
              x={node.x + 28}
              y={y + 13}
              fontSize="10"
              fontWeight={isPK ? '600' : '400'}
              fill={isPK ? colors.pkText : isFK ? colors.fkText : colors.regularColumnText}
            >
              {col.name.length > 12 ? col.name.slice(0, 10) + '..' : col.name}
            </text>
          </g>
        );
      })}

      {/* Expand/Collapse button - positioned at bottom right */}
      {enableExpand && (hasMore || isExpanded) && (
        <g onClick={(e) => onToggleExpand(node.table.name, e)} className="cursor-pointer">
          <title>{hasMore ? `Show ${node.table.columns.length - keyColumns.length} more columns` : 'Collapse'}</title>
          <rect
            x={node.x + node.width - 28}
            y={node.y + headerHeight + displayColumns.length * columnHeight + 2}
            width={24}
            height={16}
            fill={colors.expandButtonBg}
            rx="2"
          />
          <foreignObject
            x={node.x + node.width - 24}
            y={node.y + headerHeight + displayColumns.length * columnHeight + 2}
            width={16}
            height={16}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              {hasMore ? (
                <ChevronDown size={14} color={colors.expandButtonText} />
              ) : (
                <ChevronUp size={14} color={colors.expandButtonText} />
              )}
            </div>
          </foreignObject>
        </g>
      )}

      {/* Clickable header overlay */}
      <rect
        x={node.x}
        y={node.y}
        width={node.width}
        height={headerHeight}
        fill="transparent"
        className="cursor-pointer"
        onClick={handleHeaderClick}
        onMouseDown={handleDragStart}
      />
    </g>
  );
}

