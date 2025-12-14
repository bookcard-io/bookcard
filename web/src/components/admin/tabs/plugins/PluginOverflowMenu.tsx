"use client";

import { useCallback } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import type { PluginOverflowAction } from "./pluginActions";

export interface PluginOverflowMenuProps {
  isOpen: boolean;
  onClose: () => void;
  buttonRef: React.RefObject<HTMLElement | null>;
  cursorPosition: { x: number; y: number } | null;
  ariaLabel: string;
  actions: PluginOverflowAction[];
}

/**
 * Overflow menu for plugin card actions.
 *
 * Centralizes menu rendering and click-to-close behavior.
 */
export function PluginOverflowMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  ariaLabel,
  actions,
}: PluginOverflowMenuProps): React.ReactElement {
  const handleItemClick = useCallback(
    (handler: () => void) => {
      handler();
      onClose();
    },
    [onClose],
  );

  return (
    <DropdownMenu
      isOpen={isOpen}
      onClose={onClose}
      buttonRef={buttonRef}
      cursorPosition={cursorPosition}
      ariaLabel={ariaLabel}
      horizontalAlign="right"
      autoFlipHorizontal
    >
      {actions.map((action) => (
        <DropdownMenuItem
          key={action.label}
          icon={action.icon}
          label={action.label}
          onClick={
            action.disabled ? undefined : () => handleItemClick(action.onClick)
          }
          disabled={action.disabled}
          className={
            action.tone === "danger"
              ? "text-[var(--color-danger-a10)]"
              : undefined
          }
        />
      ))}
    </DropdownMenu>
  );
}
