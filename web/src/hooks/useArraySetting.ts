import { useEffect, useRef } from "react";
import { useSettings } from "@/contexts/SettingsContext";

export interface UseArraySettingOptions<T> {
  /**
   * Setting key to load and save.
   */
  key: string;
  /**
   * Default value if setting is not found.
   */
  defaultValue: T[];
  /**
   * Current array value (from external state management).
   */
  value: T[];
  /**
   * Function to update the array value.
   */
  setValue: (value: T[]) => void;
}

/**
 * Custom hook for managing an array setting stored as JSON.
 *
 * Handles loading and saving array settings with JSON serialization.
 * Prevents save during initial load to avoid unnecessary API calls.
 * Follows SRP by handling only array setting persistence logic.
 * Follows IOC by using settings context for persistence.
 *
 * Parameters
 * ----------
 * options : UseArraySettingOptions<T>
 *     Configuration including setting key, default value, and state management.
 */
export function useArraySetting<T>({
  key,
  defaultValue,
  value,
  setValue,
}: UseArraySettingOptions<T>): void {
  const { getSetting, updateSetting, isLoading } = useSettings();
  const isInitialLoadRef = useRef(true);
  const previousValueRef = useRef<T[]>(defaultValue);

  // Load setting value on mount or when settings are loaded
  useEffect(() => {
    if (!isLoading && isInitialLoadRef.current) {
      const savedValue = getSetting(key);
      if (savedValue) {
        try {
          const parsed = JSON.parse(savedValue) as T[];
          if (Array.isArray(parsed)) {
            previousValueRef.current = parsed;
            setValue(parsed);
          }
        } catch {
          // Invalid JSON, use default
          previousValueRef.current = defaultValue;
          setValue(defaultValue);
        }
      } else {
        previousValueRef.current = defaultValue;
      }
      // Mark initial load as complete after settings are loaded
      setTimeout(() => {
        isInitialLoadRef.current = false;
      }, 0);
    }
  }, [getSetting, isLoading, key, defaultValue, setValue]);

  // Save changes when value changes (but not during initial load)
  useEffect(() => {
    if (!isInitialLoadRef.current && !isLoading) {
      // Only save if value actually changed
      const currentJson = JSON.stringify([...value].sort());
      const previousJson = JSON.stringify([...previousValueRef.current].sort());
      if (currentJson !== previousJson) {
        updateSetting(key, JSON.stringify(value));
        previousValueRef.current = [...value];
      }
    }
  }, [value, updateSetting, isLoading, key]);
}
