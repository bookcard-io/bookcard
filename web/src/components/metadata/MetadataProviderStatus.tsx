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

"use client";

import type { ProviderStatus } from "@/hooks/useMetadataSearchStream";

export interface MetadataProviderStatusProps {
  /** Provider status information. */
  status: ProviderStatus;
  /** Whether the provider is preferred (sent to backend). */
  enabled: boolean;
  /** Callback when preferred toggle is clicked. */
  onToggle: () => void;
  /** Callback to scroll to provider's first result. */
  onScrollToResults?: () => void;
}

/**
 * Component for displaying individual provider search status.
 *
 * Follows SRP by focusing solely on provider status visualization.
 */
export function MetadataProviderStatus({
  status,
  enabled,
  onToggle,
  onScrollToResults,
}: MetadataProviderStatusProps) {
  const getStatusIcon = () => {
    switch (status.status) {
      case "pending":
        return (
          <i
            className="pi pi-hourglass text-text-a30 text-xl"
            aria-hidden="true"
          />
        );
      case "searching":
        return (
          <i
            className="pi pi-spin pi-spinner text-primary-a0 text-xl"
            aria-hidden="true"
          />
        );
      case "completed":
        return (
          <i
            className="pi pi-check text-success-a0 text-xl"
            aria-hidden="true"
          />
        );
      case "failed":
        return (
          <i
            className="pi pi-asterisk text-danger-a0 text-xl"
            aria-hidden="true"
          />
        );
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case "pending":
        return "Waiting...";
      case "searching":
        return status.discovered > 0
          ? `Found ${status.discovered}...`
          : "Searching...";
      case "completed": {
        const resultText = `${status.resultCount} result${status.resultCount !== 1 ? "s" : ""}`;
        if (status.resultCount > 0 && onScrollToResults) {
          return (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onScrollToResults();
              }}
              className="m-0 cursor-pointer border-0 bg-transparent p-0 font-inherit text-inherit transition-[color,opacity] duration-200 hover:text-primary-a0 hover:opacity-100 focus:rounded-sm focus:outline-none focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2"
              title={`Scroll to ${status.name} results`}
            >
              {resultText}
            </button>
          );
        }
        return resultText;
      }
      case "failed": {
        // Show brief error message if available
        if (status.error) {
          // Truncate long error messages
          const maxLength = 50;
          const truncated =
            status.error.length > maxLength
              ? `${status.error.slice(0, maxLength)}...`
              : status.error;
          return (
            <span className="text-danger-a10" title={status.error}>
              {truncated}
            </span>
          );
        }
        return <span className="text-danger-a10">Failed</span>;
      }
      default:
        return "";
    }
  };

  return (
    <div
      className="flex flex-col gap-[0.35rem] rounded-md border border-surface-a20 bg-surface-a10 p-2 transition-all duration-200 data-[status=completed]:border-success-a0 data-[status=failed]:border-danger-a0 data-[status=searching]:border-primary-a0 data-[status=completed]:bg-[rgba(34,148,110,0.1)] data-[status=failed]:bg-[rgba(156,33,33,0.15)] data-[status=searching]:bg-[rgba(144,170,249,0.1)] data-[enabled=false]:opacity-60"
      data-status={status.status}
      data-enabled={enabled}
    >
      <div className="flex items-center gap-2">
        <div className="flex w-8 shrink-0 flex-col items-center justify-center gap-1">
          {getStatusIcon()}
          <button
            type="button"
            className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-0 transition-transform duration-200 hover:scale-110 active:scale-95"
            onClick={onToggle}
            aria-label={
              enabled
                ? `Unmark ${status.name} as preferred`
                : `Mark ${status.name} as preferred`
            }
            aria-pressed={enabled}
            title={enabled ? "Unmark as preferred" : "Mark as preferred"}
          >
            <i
              className={`pi ${enabled ? "pi-check-circle" : "pi-circle"} text-sm transition-colors duration-200 ${enabled ? "text-success-a0" : "text-text-a30"}`}
              aria-hidden="true"
            />
          </button>
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <div className="font-medium text-[0.825rem] text-text-a0">
            {status.name}
          </div>
          <div className="text-[0.7rem] text-text-a30">{getStatusText()}</div>
        </div>
        {status.status === "completed" &&
          status.resultCount > 0 &&
          onScrollToResults && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onScrollToResults();
              }}
              className="cursor-pointer rounded-full border border-surface-a30 bg-surface-a20 px-2 py-0.5 font-medium text-[0.65rem] text-text-a20 uppercase leading-none transition-colors duration-200 hover:border-primary-a0 hover:bg-primary-a0/20 hover:text-primary-a0 focus:outline-none focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2"
              title={`Scroll to ${status.name} results`}
            >
              Results
            </button>
          )}
        {status.durationMs !== undefined && status.status === "completed" && (
          <div className="whitespace-nowrap text-text-a30 text-xs">
            {(status.durationMs / 1000).toFixed(1)}s
          </div>
        )}
      </div>
      {status.status === "failed" && status.error && (
        <div
          className="mt-1 rounded border border-danger-a0/30 bg-[rgba(156,33,33,0.15)] p-2 text-[0.7rem] text-danger-a10"
          role="alert"
          aria-live="polite"
        >
          <div className="flex items-start gap-1.5">
            <i
              className="pi pi-exclamation-triangle mt-0.5 shrink-0 text-danger-a0"
              aria-hidden="true"
            />
            <div className="min-w-0 flex-1">
              {status.errorType && (
                <div className="mb-0.5 font-semibold text-danger-a0">
                  {status.errorType}
                </div>
              )}
              <div className="break-words">{status.error}</div>
            </div>
          </div>
        </div>
      )}
      {status.status === "searching" && status.discovered > 0 && (
        <div className="mt-1 h-1 w-full overflow-hidden rounded-[0.125rem] bg-surface-a20">
          <div
            className="h-full rounded-[0.125rem] bg-primary-a0 transition-[width] duration-300 ease-in-out"
            style={{
              width: `${Math.min((status.discovered / 20) * 100, 100)}%`,
            }}
          />
        </div>
      )}
    </div>
  );
}
