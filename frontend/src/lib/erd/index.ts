/**
 * ERD Library
 * A reusable Entity-Relationship Diagram library
 * 
 * Features:
 * - Pan and zoom functionality
 * - Draggable table nodes
 * - Table selection with highlighting
 * - Configurable colors and opacity
 * - Line crossing bridges
 * - Expand/collapse for columns
 * - Save diagram state
 * 
 * Usage:
 * ```tsx
 * import { ERDContainer } from '@/lib/erd';
 *
 * <ERDContainer
 *   tables={tables}
 *   config={{
 *     colors: { relationshipLine: '#ff0000' },
 *     enableDragging: true,
 *     enableSave: true,
 *   }}
 *   onTableClick={(tableName) => handleTableClick(tableName)}
 *   onSave={(event) => savePositions(event.nodes)}
 * />
 * ```
 */

// Components
export { ERDContainer, ERDTable, ERDRelationship, ERDControls, ERDMarkers } from './components';

// Contexts
export { ERDSettingsProvider, useERDSettings } from './contexts';

// Hooks
export { usePanZoom, useDrag, useSelection } from './hooks';

// Configuration
export { DEFAULT_COLORS, DEFAULT_LAYOUT, DEFAULT_ZOOM, DEFAULT_CONFIG, mergeConfig } from './config';

// Types
export type {
  // Core types
  Position,
  Transform,
  ERDNode,
  ERDRelationship as ERDRelationshipType,
  PathSegment,
  CrossingPoint,
  // Config types
  ERDColors,
  ERDLayoutConfig,
  ERDZoomConfig,
  ERDConfig,
  ERDSettings,
  // Event types
  ERDTableClickEvent,
  ERDSaveEvent,
  ERDDragEvent,
  // Props types
  ERDContainerProps,
} from './types';

// Utilities
export {
  // Constants
  DEFAULT_VIEWPORT_WIDTH,
  DEFAULT_VIEWPORT_HEIGHT,
  // Functions
  getColumnYPosition,
  getPathSegments,
  findCrossing,
  generatePathWithBridges,
  generateSimplePath,
  getKeyColumns,
  calculateNodeHeight,
  extractRelationships,
  buildAdjacencyMap,
  sortTablesByConnectivity,
  calculateGridLayout,
  groupRelationshipsByPair,
  getConnectedTables,
  isRelationshipConnected,
} from './utils';

