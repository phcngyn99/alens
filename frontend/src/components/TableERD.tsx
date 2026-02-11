import { useMemo } from 'react';
import type { Table, ForeignKey } from '../types';

interface TableERDProps {
  selectedTable: Table;
  relatedTables: Table[];
  onTableClick?: (tableName: string) => void;
}

interface TableNode {
  table: Table;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Relationship {
  from: string;
  to: string;
  fk: ForeignKey;
}

export default function TableERD({ selectedTable, relatedTables, onTableClick }: TableERDProps) {
  const { nodes, relationships, svgWidth, svgHeight } = useMemo(() => {
    const nodeWidth = 200;
    const nodeHeaderHeight = 32;
    const nodeColumnHeight = 24;
    const horizontalGap = 100;
    const verticalGap = 40;
    const centerX = 400;
    const centerY = 50;

    // Calculate node dimensions
    const calcNodeHeight = (table: Table) => 
      nodeHeaderHeight + Math.min(table.columns.length, 8) * nodeColumnHeight + 16;

    // Create center node for selected table
    const centerNode: TableNode = {
      table: selectedTable,
      x: centerX - nodeWidth / 2,
      y: centerY,
      width: nodeWidth,
      height: calcNodeHeight(selectedTable),
    };

    const nodes: TableNode[] = [centerNode];
    const relationships: Relationship[] = [];

    // Add outgoing FK relationships (tables this table references)
    const outgoing = selectedTable.foreign_keys.map(fk => fk.referenced_table);
    
    // Add incoming FK relationships (tables that reference this table)
    const incoming: { table: Table; fk: ForeignKey }[] = [];
    relatedTables.forEach(t => {
      t.foreign_keys.forEach(fk => {
        if (fk.referenced_table === selectedTable.name && fk.referenced_schema === selectedTable.schema_name) {
          incoming.push({ table: t, fk });
        }
      });
    });

    // Position outgoing tables (referenced by selected) on the right
    const outgoingTables = relatedTables.filter(t => outgoing.includes(t.name));
    outgoingTables.forEach((table, idx) => {
      const height = calcNodeHeight(table);
      const y = centerY + idx * (height + verticalGap);
      nodes.push({
        table,
        x: centerX + nodeWidth / 2 + horizontalGap,
        y,
        width: nodeWidth,
        height,
      });
      // Find the FK
      const fk = selectedTable.foreign_keys.find(f => f.referenced_table === table.name);
      if (fk) {
        relationships.push({ from: selectedTable.name, to: table.name, fk });
      }
    });

    // Position incoming tables (referencing selected) on the left
    const incomingTableNames = new Set(incoming.map(i => i.table.name));
    const incomingTables = relatedTables.filter(t => incomingTableNames.has(t.name));
    incomingTables.forEach((table, idx) => {
      const height = calcNodeHeight(table);
      const y = centerY + idx * (height + verticalGap);
      nodes.push({
        table,
        x: centerX - nodeWidth / 2 - horizontalGap - nodeWidth,
        y,
        width: nodeWidth,
        height,
      });
      const rel = incoming.find(i => i.table.name === table.name);
      if (rel) {
        relationships.push({ from: table.name, to: selectedTable.name, fk: rel.fk });
      }
    });

    // Calculate SVG dimensions
    const allX = nodes.map(n => [n.x, n.x + n.width]).flat();
    const allY = nodes.map(n => [n.y, n.y + n.height]).flat();
    const svgWidth = Math.max(...allX) - Math.min(...allX) + 100;
    const svgHeight = Math.max(...allY) + 50;

    // Normalize positions
    const minX = Math.min(...nodes.map(n => n.x));
    nodes.forEach(n => { n.x -= minX - 50; });

    return { nodes, relationships, svgWidth, svgHeight };
  }, [selectedTable, relatedTables]);

  const getNodeByName = (name: string) => nodes.find(n => n.table.name === name);

  return (
    <div className="border rounded-lg bg-gray-50 overflow-auto" style={{ maxHeight: '400px' }}>
      <svg width={svgWidth} height={svgHeight} className="min-w-full">
        {/* Draw relationship lines */}
        {relationships.map((rel, idx) => {
          const fromNode = getNodeByName(rel.from);
          const toNode = getNodeByName(rel.to);
          if (!fromNode || !toNode) return null;
          
          const x1 = fromNode.x + fromNode.width;
          const y1 = fromNode.y + 40;
          const x2 = toNode.x;
          const y2 = toNode.y + 40;
          
          return (
            <g key={idx}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrow)" />
              <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 8} textAnchor="middle" className="text-xs fill-gray-600">
                {rel.fk.columns.join(', ')}
              </text>
            </g>
          );
        })}
        
        {/* Arrow marker definition */}
        <defs>
          <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#6366f1" />
          </marker>
        </defs>
        
        {/* Draw table nodes */}
        {nodes.map((node, idx) => {
          const isSelected = node.table.name === selectedTable.name;
          return (
            <g key={idx} onClick={() => onTableClick?.(node.table.name)} className="cursor-pointer">
              <rect x={node.x} y={node.y} width={node.width} height={node.height} 
                fill={isSelected ? '#e0e7ff' : 'white'} stroke={isSelected ? '#6366f1' : '#d1d5db'} 
                strokeWidth={isSelected ? 2 : 1} rx="4" />
              <rect x={node.x} y={node.y} width={node.width} height={32} 
                fill={isSelected ? '#6366f1' : '#f3f4f6'} rx="4" />
              <text x={node.x + node.width / 2} y={node.y + 20} textAnchor="middle" 
                className={`text-sm font-semibold ${isSelected ? 'fill-white' : 'fill-gray-700'}`}>
                {node.table.name}
              </text>
              {node.table.columns.slice(0, 8).map((col, cidx) => (
                <text key={cidx} x={node.x + 8} y={node.y + 48 + cidx * 24} className="text-xs fill-gray-600">
                  {col.is_primary_key ? '🔑 ' : col.is_foreign_key ? '🔗 ' : '   '}
                  {col.name}
                </text>
              ))}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

