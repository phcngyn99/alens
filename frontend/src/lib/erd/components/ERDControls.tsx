/**
 * ERDControls Component
 * Zoom controls and optional save button for the ERD diagram
 */

import { ZoomIn, ZoomOut, Maximize2, Save } from 'lucide-react';

interface ERDControlsProps {
  zoomPercentage: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  showSaveButton?: boolean;
  onSave?: () => void;
  isSaving?: boolean;
}

export function ERDControls({
  zoomPercentage,
  onZoomIn,
  onZoomOut,
  onResetView,
  showSaveButton = false,
  onSave,
  isSaving = false,
}: ERDControlsProps) {
  return (
    <div className="absolute top-2 right-2 z-10 flex gap-1 bg-white rounded-lg shadow-md border border-gray-200 p-1">
      <button
        onClick={onZoomIn}
        className="p-1.5 hover:bg-gray-100 rounded transition-colors"
        title="Zoom in"
        aria-label="Zoom in"
      >
        <ZoomIn size={16} className="text-gray-600" />
      </button>
      <button
        onClick={onZoomOut}
        className="p-1.5 hover:bg-gray-100 rounded transition-colors"
        title="Zoom out"
        aria-label="Zoom out"
      >
        <ZoomOut size={16} className="text-gray-600" />
      </button>
      <button
        onClick={onResetView}
        className="p-1.5 hover:bg-gray-100 rounded transition-colors"
        title="Reset view"
        aria-label="Reset view"
      >
        <Maximize2 size={16} className="text-gray-600" />
      </button>
      <span className="px-2 py-1 text-xs text-gray-500 border-l border-gray-200 ml-1">
        {zoomPercentage}%
      </span>
      
      {showSaveButton && (
        <>
          <div className="border-l border-gray-200 ml-1" />
          <button
            onClick={onSave}
            disabled={isSaving}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
            title="Save diagram positions"
            aria-label="Save diagram"
          >
            <Save size={16} className={isSaving ? 'text-gray-400' : 'text-gray-600'} />
          </button>
        </>
      )}
    </div>
  );
}

