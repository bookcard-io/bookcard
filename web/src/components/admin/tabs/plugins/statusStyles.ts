import type { PluginStatusType } from "@/utils/plugins/errorHandling";

export interface StatusStyles {
  border: string;
  bg: string;
  text: string;
  icon: string;
}

export const statusStyleMap: Record<PluginStatusType, StatusStyles> = {
  error: {
    border: "border-[var(--color-danger-a0)]",
    bg: "bg-[var(--color-danger-a20)]",
    text: "text-[var(--color-danger-a0)]",
    icon: "pi-exclamation-triangle",
  },
  warning: {
    border: "border-[var(--color-warning-a0)]",
    bg: "bg-[var(--color-warning-a20)]",
    text: "text-[var(--color-warning-a0)]",
    icon: "pi-exclamation-triangle",
  },
  success: {
    border: "border-[var(--color-success-a0)]",
    bg: "bg-[var(--color-success-a20)]",
    text: "text-[var(--color-success-a0)]",
    icon: "pi-check-circle",
  },
  info: {
    border: "border-[var(--color-primary-a0)]",
    bg: "bg-[var(--color-primary-a20)]",
    text: "text-[var(--color-primary-a0)]",
    icon: "pi-info-circle",
  },
  neutral: {
    border: "border-[var(--color-surface-a20)]",
    bg: "bg-[var(--color-surface-a10)]",
    text: "text-[var(--color-text-a0)]",
    icon: "pi-circle",
  },
};
