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

import { NextResponse } from "next/server";
import { withAuthentication } from "@/libs/middleware/withAuth";

/**
 * GET /api/plugins
 *
 * Proxies request to list all installed plugins.
 */
export const GET = withAuthentication<Record<string, never>>(
  async (ctx, _request) => {
    try {
      // Note: Backend requires trailing slash for this endpoint
      const response = await ctx.client.request("/plugins/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          { detail: data.detail || "Failed to list plugins" },
          { status: response.status },
        );
      }

      return NextResponse.json(data);
    } catch (error) {
      console.error("Error in GET /api/plugins:", error);
      return NextResponse.json(
        { detail: "Internal server error" },
        { status: 500 },
      );
    }
  },
);
