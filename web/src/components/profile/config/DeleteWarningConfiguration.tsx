"use client";

import { useBooleanSetting } from "@/hooks/useBooleanSetting";
import { useBlurAfterClick } from "../BlurAfterClickContext";

const SETTING_KEY = "always_warn_on_delete";
const DEFAULT_VALUE = true;

/**
 * Delete warning configuration component.
 *
 * Manages the "Always warn when deleting books" preference.
 * Follows SRP by handling only delete warning preference.
 * Follows IOC by using useBooleanSetting hook for persistence.
 */
export function DeleteWarningConfiguration() {
  const { value, setValue } = useBooleanSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });
  const { onBlurChange } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">
        Always warn when deleting books
      </div>
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="checkbox"
          checked={value}
          onChange={onBlurChange(() => setValue(!value))}
          className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
        />
        <span className="text-base text-text-a0">
          Show confirmation dialog before deleting books
        </span>
      </label>
    </div>
  );
}
