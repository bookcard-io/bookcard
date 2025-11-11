import { useCallback, useEffect, useRef, useState } from "react";

export interface UseCoverUrlInputOptions {
  /** Callback when input visibility changes. */
  onVisibilityChange?: (isVisible: boolean) => void;
  /** Callback when URL is submitted. */
  onSubmit?: (url: string) => void;
}

export interface UseCoverUrlInputResult {
  /** Whether the input is visible. */
  isVisible: boolean;
  /** Current input value. */
  value: string;
  /** Function to show the input. */
  show: () => void;
  /** Function to hide the input. */
  hide: () => void;
  /** Function to update the input value. */
  setValue: (value: string) => void;
  /** Ref for the input element. */
  inputRef: React.RefObject<HTMLInputElement | null>;
  /** Handler for keyboard events. */
  handleKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  /** Handler for input change events. */
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

/**
 * Custom hook for managing cover URL input state and behavior.
 *
 * Handles visibility, value, focus, and keyboard interactions.
 * Follows SRP by focusing solely on input state management.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseCoverUrlInputOptions
 *     Configuration including callbacks.
 *
 * Returns
 * -------
 * UseCoverUrlInputResult
 *     Input state and control functions.
 */
export function useCoverUrlInput(
  options: UseCoverUrlInputOptions = {},
): UseCoverUrlInputResult {
  const { onVisibilityChange, onSubmit } = options;
  const [isVisible, setIsVisible] = useState(false);
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  const show = useCallback(() => {
    setIsVisible(true);
    onVisibilityChange?.(true);
    // Focus the input after it's rendered
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  }, [onVisibilityChange]);

  const hide = useCallback(() => {
    setIsVisible(false);
    setValue("");
    onVisibilityChange?.(false);
  }, [onVisibilityChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const trimmedValue = value.trim();
        if (trimmedValue) {
          onSubmit?.(trimmedValue);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation(); // Prevent modal from closing
        hide();
      }
    },
    [value, onSubmit, hide],
  );

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  }, []);

  // Auto-focus when input becomes visible
  useEffect(() => {
    if (isVisible) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  }, [isVisible]);

  return {
    isVisible,
    value,
    show,
    hide,
    setValue,
    inputRef,
    handleKeyDown,
    handleChange,
  };
}
