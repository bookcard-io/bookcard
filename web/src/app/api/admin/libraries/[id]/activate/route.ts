import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * POST /api/admin/libraries/[id]/activate
 *
 * Proxies request to activate a library.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

    const response = await fetch(
      `${BACKEND_URL}/admin/libraries/${id}/activate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to activate library" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
