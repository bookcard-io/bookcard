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

import { Button } from "@/components/forms/Button";

interface ErrorStateProps {
  error?: Error | null;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  error,
  message = "Something went wrong",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-4 text-center">
      <div className="mb-4 text-red-500 dark:text-red-400">
        <svg
          className="mx-auto h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
          role="img"
          aria-label="Error icon"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="mb-2 font-medium text-gray-900 text-lg dark:text-gray-100">
        {message}
      </h3>
      {error && (
        <p className="mb-6 max-w-sm text-gray-500 dark:text-gray-400">
          {error.message}
        </p>
      )}
      {onRetry && (
        <Button onClick={onRetry} variant="primary">
          Try Again
        </Button>
      )}
    </div>
  );
}
