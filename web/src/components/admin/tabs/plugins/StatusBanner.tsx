import { cn } from "@/libs/utils";
import type { PluginStatusType } from "@/utils/plugins/errorHandling";
import { statusStyleMap } from "./statusStyles";

export interface StatusBannerProps {
  message: string;
  type: PluginStatusType;
  onDismiss: () => void;
}

export function StatusBanner({
  message,
  type,
  onDismiss,
}: StatusBannerProps): React.ReactElement {
  const styles = statusStyleMap[type];

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border p-4",
        styles.border,
        styles.bg,
        styles.text,
      )}
    >
      <i className={cn("pi mt-0.5 flex-shrink-0", styles.icon)} />
      <div className="flex-1 text-sm">{message}</div>
      <button
        type="button"
        onClick={onDismiss}
        className="flex-shrink-0 text-current opacity-70 transition-opacity hover:opacity-100"
        aria-label="Dismiss message"
      >
        <i className="pi pi-times" />
      </button>
    </div>
  );
}
