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

import type { NextRequest } from "next/server";
import { AUTH_COOKIE_NAME } from "@/constants/config";

/**
 * Extracts authentication token from request cookies.
 *
 * Follows SRP by handling only token extraction.
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The request to extract token from.
 *
 * Returns
 * -------
 * string | undefined
 *     The authentication token, or undefined if not present.
 */
export function getAuthToken(req: NextRequest): string | undefined {
  return req.cookies.get(AUTH_COOKIE_NAME)?.value;
}
