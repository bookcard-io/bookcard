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
 * DELETE /api/plugins/[plugin_name]
 *
 * Proxies request to remove an installed plugin.
 */
export const DELETE = withAuthentication<{ plugin_name: string }>(
  async (ctx, _request, context) => {
    try {
      const { plugin_name } = await context.params;
      const encodedPluginName = encodeURIComponent(plugin_name);

      const response = await ctx.client.request(
        `/plugins/${encodedPluginName}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        const data = await response.json();
        return NextResponse.json(
          { detail: data.detail || "Failed to remove plugin" },
          { status: response.status },
        );
      }

      return new NextResponse(null, { status: 204 });
    } catch (error) {
      console.error("Error in DELETE /api/plugins/[plugin_name]:", error);
      return NextResponse.json(
        { detail: "Internal server error" },
        { status: 500 },
      );
    }
  },
);
