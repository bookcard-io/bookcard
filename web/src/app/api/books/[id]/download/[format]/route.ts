import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

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
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const { id, format: fileFormat } = await params;

    const url = new URL(`${BACKEND_URL}/books/${id}/download/${fileFormat}`);

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

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
