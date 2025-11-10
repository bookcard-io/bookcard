import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

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
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const { hash_and_ext } = await params;

    const response = await fetch(
      `${BACKEND_URL}/books/temp-covers/${hash_and_ext}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
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
