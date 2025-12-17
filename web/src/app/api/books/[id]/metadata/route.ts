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

import { type NextRequest, NextResponse } from "next/server";
import { getOptionalClient } from "@/services/http/routeHelpers";

/**
 * GET /api/books/[id]/metadata
 *
 * Proxies request to download book metadata in the specified format.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getOptionalClient(request);

    if (error) {
      return error;
    }

    const { id } = await params;
    const { searchParams } = new URL(request.url);
    const format = searchParams.get("format") || "opf";

    const response = await client.request(
      `/books/${id}/metadata?format=${format}`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      const data = await response
        .json()
        .catch(() => ({ detail: "Download failed" }));
      return NextResponse.json(
        { detail: data.detail || "Failed to download metadata" },
        { status: response.status },
      );
    }

    // Get the file content
    const blob = await response.blob();
    const contentType =
      response.headers.get("content-type") ||
      (format === "json"
        ? "application/json"
        : format === "yaml"
          ? "text/yaml"
          : "application/oebps-package+xml");
    const contentDisposition = response.headers.get("content-disposition");

    // Determine default filename based on format
    const defaultFilename =
      format === "json"
        ? "metadata.json"
        : format === "yaml"
          ? "metadata.yaml"
          : "metadata.opf";

    // Create response with file
    const fileResponse = new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition":
          contentDisposition || `attachment; filename="${defaultFilename}"`,
      },
    });

    return fileResponse;
  } catch (error) {
    console.error("Metadata download error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
