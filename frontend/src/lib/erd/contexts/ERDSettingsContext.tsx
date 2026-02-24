/**
 * ERD Settings Context
 * Centralized settings management for ERD components
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ERDSettings } from '../types';

/**
 * Default ERD settings
 */
const DEFAULT_SETTINGS: ERDSettings = {
  primaryColor: '#3b82f6', // Blue
  grayscaleEnabled: true,
  grayscaleOpacity: 0.25, // 25% opacity
};

/**
 * Settings context type
 */
interface ERDSettingsContextType {
  settings: ERDSettings;
  updateSettings: (updates: Partial<ERDSettings>) => void;
  resetSettings: () => void;
}

/**
 * Settings context
 */
const ERDSettingsContext = createContext<ERDSettingsContextType | undefined>(undefined);

/**
 * Settings provider props
 */
interface ERDSettingsProviderProps {
  children: ReactNode;
  initialSettings?: Partial<ERDSettings>;
}

/**
 * Settings provider component
 */
export const ERDSettingsProvider: React.FC<ERDSettingsProviderProps> = ({
  children,
  initialSettings,
}) => {
  const [settings, setSettings] = useState<ERDSettings>({
    ...DEFAULT_SETTINGS,
    ...initialSettings,
  });

  const updateSettings = (updates: Partial<ERDSettings>) => {
    setSettings((prev: ERDSettings) => ({
      ...prev,
      ...updates,
    }));
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <ERDSettingsContext.Provider value={{ settings, updateSettings, resetSettings }}>
      {children}
    </ERDSettingsContext.Provider>
  );
};

/**
 * Hook to use ERD settings
 */
export const useERDSettings = (): ERDSettingsContextType => {
  const context = useContext(ERDSettingsContext);
  if (!context) {
    throw new Error('useERDSettings must be used within ERDSettingsProvider');
  }
  return context;
};

