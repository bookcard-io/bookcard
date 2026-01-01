"use client";

import type { IconType } from "react-icons";
import { Tooltip } from "@/components/layout/Tooltip";
import { cn } from "@/libs/utils";

interface IconButtonProps {
  icon: IconType;
  tooltip?: string;
  onClick?: () => void;
  variant?: "default" | "danger";
  className?: string;
}

const ICON_BUTTON_VARIANTS = {
  default: "text-text-a20 hover:bg-surface-a20 hover:text-text-a0",
  danger: "text-text-a20 hover:bg-surface-a20 hover:text-danger-a10",
};

export function IconButton({
  icon: Icon,
  tooltip,
  onClick,
  variant = "default",
  className,
}: IconButtonProps) {
  const button = (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-10 w-10 items-center justify-center rounded-full transition-colors",
        ICON_BUTTON_VARIANTS[variant],
        className,
      )}
    >
      <Icon className="text-lg" />
    </button>
  );

  if (tooltip) {
    return <Tooltip text={tooltip}>{button}</Tooltip>;
  }

  return button;
}
