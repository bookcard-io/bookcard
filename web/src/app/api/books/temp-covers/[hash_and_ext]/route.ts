import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/books/temp-covers/[hash_and_ext]
 *
 * Proxies request to get temporary cover image.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ hash_and_ext: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { hash_and_ext } = await params;

    const response = await client.request(
      `/books/temp-covers/${hash_and_ext}`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      return NextResponse.json(
        { detail: "Failed to fetch temporary cover" },
        { status: response.status },
      );
    }

    // Return the image file
    const imageBuffer = await response.arrayBuffer();
    return new NextResponse(imageBuffer, {
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "image/jpeg",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
