// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

export type StatusPillVariant = "success" | "warning" | "danger" | "info";

export interface StatusPillProps {
  /** Text to display in the pill. */
  label: string;
  /** Icon class name (e.g., "pi pi-check"). */
  icon?: string;
  /** Background color for the icon circle. */
  iconBgColor?: string;
  /** Color variant for the pill background. */
  variant?: StatusPillVariant;
  /** Custom background color (overrides variant). */
  bgColor?: string;
}

/**
 * Generic status pill component.
 *
 * Displays a pill-shaped badge with optional icon and text.
 * Follows SRP by handling only pill rendering.
 * Follows IOC by accepting all styling via props.
 *
 * Parameters
 * ----------
 * props : StatusPillProps
 *     Component props including label, icon, and styling options.
 */
export function StatusPill({
  label,
  icon,
  iconBgColor,
  variant = "success",
  bgColor,
}: StatusPillProps) {
  // Get background color from variant or use custom
  const getBackgroundColor = () => {
    if (bgColor) return bgColor;
    switch (variant) {
      case "success":
        return "var(--color-success-a10)";
      case "warning":
        return "var(--color-warning-a10)";
      case "danger":
        return "var(--color-danger-a10)";
      case "info":
        return "var(--color-info-a10)";
      default:
        return "var(--color-success-a10)";
    }
  };

  // Get icon background color from variant or use custom
  const getIconBackgroundColor = () => {
    if (iconBgColor) return iconBgColor;
    switch (variant) {
      case "success":
        return "var(--color-success-a0)";
      case "warning":
        return "var(--color-warning-a0)";
      case "danger":
        return "var(--color-danger-a0)";
      case "info":
        return "var(--color-info-a0)";
      default:
        return "var(--color-success-a0)";
    }
  };

  return (
    <div
      className="flex items-center gap-2 rounded-full px-3 py-1.5"
      style={{ backgroundColor: getBackgroundColor() }}
    >
      {icon && (
        <div
          className="flex h-5 w-5 items-center justify-center rounded-full"
          style={{ backgroundColor: getIconBackgroundColor() }}
        >
          <i className={`${icon} text-[var(--color-white)] text-xs`} />
        </div>
      )}
      <span
        className="font-medium text-sm"
        style={{ color: "var(--color-black)" }}
      >
        {label}
      </span>
    </div>
  );
}
