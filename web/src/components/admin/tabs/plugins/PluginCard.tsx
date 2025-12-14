import { useCallback, useMemo, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import type { PluginInfo } from "@/services/pluginService";
import { PluginOverflowMenu } from "./PluginOverflowMenu";
import type {
  PluginOverflowAction,
  PluginPrimaryAction,
} from "./pluginActions";

export interface PluginCardProps {
  plugin: PluginInfo;
  installing: boolean;
  primaryAction?: PluginPrimaryAction;
  overflowActions: PluginOverflowAction[];
  onRemove: (pluginName: string) => void;
}

export function PluginCard({
  plugin,
  installing,
  primaryAction,
  overflowActions,
  onRemove,
}: PluginCardProps): React.ReactElement {
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const actions = useMemo<PluginOverflowAction[]>(() => {
    const removeAction: PluginOverflowAction = {
      label: "Remove",
      icon: "pi pi-trash",
      tone: "danger",
      disabled: installing,
      onClick: () => onRemove(plugin.name),
    };

    return [...overflowActions, removeAction];
  }, [installing, onRemove, overflowActions, plugin.name]);

  const toggleMenu = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    setCursorPosition({ x: e.clientX, y: e.clientY });
    setIsMenuOpen((prev) => !prev);
  }, []);

  const closeMenu = useCallback(() => {
    setIsMenuOpen(false);
  }, []);

  return (
    <div className="flex items-stretch justify-between rounded-md border border-[var(--color-surface-a10)] bg-[var(--color-surface-a0)] p-4">
      <div className="self-start">
        <div className="flex items-baseline gap-2">
          <h3 className="font-bold text-[var(--color-text-a0)]">
            {plugin.name}
          </h3>
          <span className="text-[var(--color-text-a40)] text-xs">
            v{plugin.version}
          </span>
        </div>
        <div className="mb-1 text-[var(--color-text-a20)] text-sm">
          by {plugin.author}
        </div>
        <p className="text-[var(--color-text-a30)] text-sm">
          {plugin.description}
        </p>
      </div>

      <div className="ml-4 flex items-start gap-2">
        {primaryAction ? (
          <Button
            variant="primary"
            size="small"
            onClick={primaryAction.onClick}
            disabled={primaryAction.disabled}
            className="whitespace-nowrap"
          >
            {primaryAction.label}
          </Button>
        ) : null}

        <button
          ref={buttonRef}
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded border border-[var(--color-surface-a20)] bg-[var(--color-surface-a10)] text-[var(--color-text-a0)] transition-colors hover:bg-[var(--color-surface-a20)]"
          onClick={toggleMenu}
          aria-label="More actions"
          aria-haspopup="true"
          aria-expanded={isMenuOpen}
        >
          <i className="pi pi-ellipsis-v" aria-hidden="true" />
        </button>
      </div>

      <PluginOverflowMenu
        isOpen={isMenuOpen}
        onClose={closeMenu}
        buttonRef={buttonRef}
        cursorPosition={cursorPosition}
        ariaLabel={`${plugin.name} actions`}
        actions={actions}
      />
    </div>
  );
}
