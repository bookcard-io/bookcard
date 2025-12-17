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

/**
 * Centralized configuration for the web frontend.
 */

export const AUTH_COOKIE_NAME = "bookcard_token";

/**
 * Resolve the backend base URL.
 *
 * This is used by server-side API routes (Next.js API routes) to proxy requests
 * to the backend. The client never directly calls this URL.
 *
 * Order of precedence:
 * - BACKEND_URL (server-only env var, set in docker-compose or .env)
 * - NEXT_PUBLIC_BACKEND_URL (can be used in client code, but not needed here)
 * - Default based on NODE_ENV:
 *   - production: http://bookcard-backend:8000 (Docker service name)
 *   - development: http://localhost:8000 (local dev)
 *
 * Note: For local development, ensures HTTP protocol is used (not HTTPS)
 * to avoid SSL errors when connecting to local backend.
 *
 * To configure:
 * - Docker: Set BACKEND_URL in docker-compose.yaml or via .env file
 * - Local dev: Create web/.env.local with BACKEND_URL=http://localhost:8000
 */
function getBackendUrl(): string {
  const envUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
  if (envUrl) {
    // Normalize the URL
    let url = envUrl.trim();
    // If URL doesn't start with http:// or https://, prepend http://
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = `http://${url}`;
    }
    // For local development, always use HTTP for localhost to avoid SSL errors
    if (
      process.env.NODE_ENV !== "production" &&
      (url.includes("localhost") || url.includes("127.0.0.1"))
    ) {
      url = url.replace(/^https:/, "http:");
    }
    return url;
  }
  // Default based on environment
  return process.env.NODE_ENV === "production"
    ? "http://bookcard-backend:8000"
    : "http://localhost:8000";
}

export const BACKEND_URL: string = getBackendUrl();

/**
 * Whether cookies should be marked secure.
 */
export const COOKIE_SECURE: boolean = process.env.NODE_ENV === "production";
