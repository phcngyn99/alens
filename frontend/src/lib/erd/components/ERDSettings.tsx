/**
 * ERDSettings Component
 * Settings panel for controlling ERD appearance and behavior
 * 
 * Architecture: OOP-based expandable settings system
 * - Settings are organized into categories (Appearance, Effects, etc.)
 * - Each category can be expanded independently
 * - Easy to add new settings categories in the future
 */

import { useState } from 'react';
import { Settings, ChevronDown, ChevronUp } from 'lucide-react';
import { useERDSettings } from '../contexts';

// ============================================================================
// Settings Category Base Interface (OOP)
// ============================================================================

export interface SettingsCategory {
  id: string;
  name: string;
  icon?: React.ReactNode;
  expanded: boolean;
}

// ============================================================================
// ERDSettings Component
// ============================================================================

export function ERDSettings() {
  const { settings, updateSettings } = useERDSettings();
  const [isOpen, setIsOpen] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['effects']) // Effects expanded by default
  );

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryId)) {
        next.delete(categoryId);
      } else {
        next.add(categoryId);
      }
      return next;
    });
  };

  const isCategoryExpanded = (categoryId: string) => expandedCategories.has(categoryId);

  // Handle grayscale toggle
  const handleGrayscaleToggle = () => {
    updateSettings({
      grayscaleEnabled: !settings.grayscaleEnabled,
    });
  };

  // Handle grayscale opacity change
  const handleGrayscaleOpacityChange = (value: number) => {
    updateSettings({
      grayscaleOpacity: value / 100, // Convert percentage to decimal
    });
  };

  // Handle color change
  const handleColorChange = (value: string) => {
    updateSettings({
      primaryColor: value,
    });
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="absolute top-2 left-2 z-10 p-2 bg-white rounded-lg shadow-md border border-gray-200 hover:bg-gray-50 transition-colors"
        title="Open settings"
        aria-label="Open settings"
      >
        <Settings size={16} className="text-gray-600" />
      </button>
    );
  }

  return (
    <div className="absolute top-2 left-2 z-10 bg-white rounded-lg shadow-lg border border-gray-200 w-80 max-h-[500px] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 sticky top-0 bg-white">
        <div className="flex items-center gap-2">
          <Settings size={16} className="text-gray-600" />
          <h3 className="font-semibold text-sm text-gray-700">ERD Settings</h3>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close settings"
        >
          ×
        </button>
      </div>

      {/* Settings Content */}
      <div className="p-2">
        {/* Effects Category */}
        <SettingsCategorySection
          id="effects"
          name="Visual Effects"
          expanded={isCategoryExpanded('effects')}
          onToggle={() => toggleCategory('effects')}
        >
          {/* Grayscale Toggle */}
          <SettingRow label="Grayscale Effect">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.grayscaleEnabled}
                onChange={handleGrayscaleToggle}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </SettingRow>

          {/* Grayscale Opacity Slider */}
          {settings.grayscaleEnabled && (
            <SettingRow label={`Grayscale Opacity (${Math.round(settings.grayscaleOpacity * 100)}%)`}>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.grayscaleOpacity * 100}
                onChange={(e) => handleGrayscaleOpacityChange(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </SettingRow>
          )}
        </SettingsCategorySection>

        {/* Colors Category */}
        <SettingsCategorySection
          id="colors"
          name="Colors"
          expanded={isCategoryExpanded('colors')}
          onToggle={() => toggleCategory('colors')}
        >
          {/* Primary Color */}
          <SettingRow label="Primary Color">
            <input
              type="color"
              value={settings.primaryColor}
              onChange={(e) => handleColorChange(e.target.value)}
              className="w-12 h-8 rounded border border-gray-300 cursor-pointer"
            />
          </SettingRow>
        </SettingsCategorySection>
      </div>
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

interface SettingsCategorySectionProps {
  id: string;
  name: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function SettingsCategorySection({
  name,
  expanded,
  onToggle,
  children,
}: SettingsCategorySectionProps) {
  return (
    <div className="mb-2">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-2 hover:bg-gray-50 rounded transition-colors"
      >
        <span className="text-sm font-medium text-gray-700">{name}</span>
        {expanded ? (
          <ChevronUp size={14} className="text-gray-500" />
        ) : (
          <ChevronDown size={14} className="text-gray-500" />
        )}
      </button>
      {expanded && <div className="px-2 py-1 space-y-2">{children}</div>}
    </div>
  );
}

interface SettingRowProps {
  label: string;
  children: React.ReactNode;
}

function SettingRow({ label, children }: SettingRowProps) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <label className="text-xs text-gray-600">{label}</label>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}

