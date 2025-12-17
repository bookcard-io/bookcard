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

import type { RouteConfig } from "./types";

/**
 * Default route configuration.
 *
 * Centralizes all route matching patterns for maintainability.
 * Follows OCP by allowing extension through configuration.
 */
export const defaultRouteConfig: RouteConfig = {
  protectedPatterns: [
    // Admin routes - always require authentication
    /^\/admin/,
    // Profile routes - always require authentication
    /^\/profile/,
    // Book editing routes - always require authentication
    /^\/books\/.*\/edit/,
  ],
  anonymousAllowedPatterns: [
    // Home page - shows library or login prompt
    /^\/$/,
    // Book viewing routes - allowed for anonymous when enabled
    /^\/books\/.*\/view/,
    // Reading routes - allowed for anonymous when enabled
    /^\/reading/,
  ],
  staticExtensions: [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
  ],
  publicAssetPrefixes: ["/_next/", "/favicon", "/assets", "/static"],
  apiPrefixes: ["/api/"],
  authPrefixes: ["/login", "/api/auth"],
};
