import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * POST /api/auth/logout
 *
 * Proxies logout request to the backend and clears authentication cookie.
 */
export async function POST(request: NextRequest) {
  try {
    // Get Authorization header from request to forward to backend
    const authHeader = request.headers.get("Authorization");
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    // Call backend logout endpoint
    await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers,
      credentials: "include",
    });

    // Clear authentication cookie
    const nextResponse = NextResponse.json({}, { status: 204 });
    nextResponse.cookies.delete(AUTH_COOKIE_NAME);

    return nextResponse;
  } catch {
    // Even if backend call fails, clear the cookie
    const nextResponse = NextResponse.json(
      { detail: "Logout completed" },
      { status: 200 },
    );
    nextResponse.cookies.delete(AUTH_COOKIE_NAME);
    return nextResponse;
  }
}
