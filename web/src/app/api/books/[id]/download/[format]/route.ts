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
 * GET /api/books/[id]/download/[format]
 *
 * Proxies request to download a book file in the specified format.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; format: string }> },
) {
  try {
    const { client, error } = getOptionalClient(request);

    if (error) {
      return error;
    }

    const { id, format: fileFormat } = await params;

    const response = await client.request(
      `/books/${id}/download/${fileFormat}`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      const data = await response
        .json()
        .catch(() => ({ detail: "Download failed" }));
      return NextResponse.json(
        { detail: data.detail || "Failed to download file" },
        { status: response.status },
      );
    }

    // Get the file content
    const blob = await response.blob();
    // Ensure EPUB files have the correct content type
    let contentType =
      response.headers.get("content-type") || "application/octet-stream";
    if (fileFormat.toUpperCase() === "EPUB" && !contentType.includes("epub")) {
      contentType = "application/epub+zip";
    }
    const contentDisposition = response.headers.get("content-disposition");

    // Create response with file
    // Add CORS headers for EPUB readers that need to access the file
    const fileResponse = new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition":
          contentDisposition ||
          `attachment; filename="${fileFormat.toLowerCase()}"`,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Cache-Control": "public, max-age=3600",
      },
    });

    return fileResponse;
  } catch (error) {
    console.error("Download error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
