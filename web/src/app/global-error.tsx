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

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

/**
 * Global error boundary component.
 *
 * Catches React rendering errors at the root layout level that cannot be
 * caught by regular error boundaries. This component must include the full
 * HTML structure (html and body tags) as it replaces the root layout when
 * an error occurs.
 *
 * Parameters
 * ----------
 * error : Error & { digest?: string }
 *     The error that was thrown.
 * reset : () => void
 *     Function to reset the error boundary and attempt to re-render.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to Sentry
    if (!process.env.NEXT_PUBLIC_SENTRY_DISABLED) {
      Sentry.captureException(error);
    }
  }, [error]);

  return (
    <html lang="en">
      <head>
        <meta name="darkreader-lock" />
      </head>
      <body>
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
          <div className="max-w-md text-center">
            <h1 className="mb-4 font-semibold text-2xl text-text-a10">
              Something went wrong
            </h1>
            <p className="mb-6 text-base text-text-a30">
              An unexpected error occurred. The error has been reported and we
              will look into it.
            </p>
            {process.env.NODE_ENV === "development" && (
              <details className="mb-6 rounded-lg border border-danger-a0/30 bg-danger-a0/10 p-4 text-left">
                <summary className="mb-2 cursor-pointer font-medium text-danger-a10">
                  Error details (development only)
                </summary>
                <pre className="mt-2 overflow-auto text-danger-a20 text-sm">
                  {error.message}
                  {error.stack && `\n\n${error.stack}`}
                </pre>
              </details>
            )}
            <button
              type="button"
              onClick={reset}
              className="btn-tonal px-6 py-3"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
