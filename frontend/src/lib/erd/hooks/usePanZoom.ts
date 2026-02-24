/**
 * Pan and Zoom Hook for ERD
 * Handles mouse interactions for panning and zooming the diagram
 */

import { useState, useCallback, useEffect } from 'react';
import type { Transform, ERDZoomConfig } from '../types';

interface UsePanZoomOptions {
  enabled?: boolean;
  zoomConfig?: ERDZoomConfig;
  initialTransform?: Transform;
}

interface UsePanZoomReturn {
  transform: Transform;
  isPanning: boolean;
  handlers: {
    onMouseDown: (e: React.MouseEvent) => void;
    onMouseMove: (e: React.MouseEvent) => void;
    onMouseUp: () => void;
    onMouseLeave: () => void;
    onWheel: (e: React.WheelEvent) => void;
  };
  controls: {
    zoomIn: () => void;
    zoomOut: () => void;
    resetView: () => void;
  };
  zoomPercentage: number;
}

const DEFAULT_ZOOM_CONFIG: ERDZoomConfig = {
  minScale: 1.0,
  maxScale: 2.0,
  zoomStep: 0.1,
};

export function usePanZoom(options: UsePanZoomOptions = {}): UsePanZoomReturn {
  const {
    enabled = true,
    zoomConfig = DEFAULT_ZOOM_CONFIG,
    initialTransform = { x: 0, y: 0, scale: 1 },
  } = options;

  const { minScale, maxScale, zoomStep } = zoomConfig;

  const [transform, setTransform] = useState<Transform>(initialTransform);
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Zoom controls
  const zoomIn = useCallback(() => {
    if (!enabled) return;
    setTransform((prev) => ({
      ...prev,
      scale: Math.min(prev.scale + zoomStep, maxScale),
    }));
  }, [enabled, zoomStep, maxScale]);

  const zoomOut = useCallback(() => {
    if (!enabled) return;
    setTransform((prev) => ({
      ...prev,
      scale: Math.max(prev.scale - zoomStep, minScale),
    }));
  }, [enabled, zoomStep, minScale]);

  const resetView = useCallback(() => {
    if (!enabled) return;
    setTransform({ x: 0, y: 0, scale: 1 });
  }, [enabled]);

  // Mouse wheel zoom - DISABLED (zoom only through buttons)
  const onWheel = useCallback((e: React.WheelEvent) => {
    // Prevent default zoom behavior but don't apply zoom
    // Zoom is only available through the zoom buttons
    if (!enabled) return;
    e.preventDefault();
  }, [enabled]);

  // Pan handlers
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (!enabled) return;
    const target = e.target as Element;
    if (target.tagName === 'svg' || target.classList.contains('erd-background')) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
    }
  }, [enabled, transform.x, transform.y]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!enabled || !isPanning) return;
    setTransform((prev) => ({
      ...prev,
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y,
    }));
  }, [enabled, isPanning, panStart]);

  const onMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  const onMouseLeave = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Global mouse up handler
  useEffect(() => {
    const handleGlobalMouseUp = () => setIsPanning(false);
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, []);

  return {
    transform,
    isPanning,
    handlers: {
      onMouseDown,
      onMouseMove,
      onMouseUp,
      onMouseLeave,
      onWheel,
    },
    controls: {
      zoomIn,
      zoomOut,
      resetView,
    },
    zoomPercentage: Math.round(transform.scale * 100),
  };
}

