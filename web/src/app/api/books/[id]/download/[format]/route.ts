import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

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
    const { client, error } = getAuthenticatedClient(request);

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
    const contentType =
      response.headers.get("content-type") || "application/octet-stream";
    const contentDisposition = response.headers.get("content-disposition");

    // Create response with file
    const fileResponse = new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition":
          contentDisposition ||
          `attachment; filename="${fileFormat.toLowerCase()}"`,
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
