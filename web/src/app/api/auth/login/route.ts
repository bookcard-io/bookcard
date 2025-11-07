import { type NextRequest, NextResponse } from "next/server";
import {
  AUTH_COOKIE_NAME,
  BACKEND_URL,
  COOKIE_SECURE,
} from "@/constants/config";

/**
 * POST /api/auth/login
 *
 * Proxies login request to the backend and sets authentication cookie.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Login failed" },
        { status: response.status },
      );
    }

    const nextResponse = NextResponse.json(data);

    // Set authentication cookie
    if (data.access_token) {
      nextResponse.cookies.set(AUTH_COOKIE_NAME, data.access_token, {
        httpOnly: true,
        secure: COOKIE_SECURE,
        sameSite: "lax",
        path: "/",
      });
    }

    return nextResponse;
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
