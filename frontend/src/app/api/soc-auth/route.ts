import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.API_BASE_URL ||
  "https://hares-api.onrender.com";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const passkey = (body.passkey || "").trim();

    if (!passkey) {
      return NextResponse.json(
        { authenticated: false, detail: "Security clearance passkey required." },
        { status: 401 }
      );
    }

    // 1. Direct validation if server-side environment variables are defined
    const serverPass = process.env.SOC_ADMIN_PASSWORD;
    const analystKey = process.env.ANALYST_API_KEY;

    if (serverPass && passkey === serverPass) {
      return NextResponse.json({
        status: "authenticated",
        authenticated: true,
        role: "soc_analyst",
        jurisdiction: "Dubai & UAE",
        timestamp: new Date().toISOString(),
      });
    }

    if (analystKey && passkey === analystKey) {
      return NextResponse.json({
        status: "authenticated",
        authenticated: true,
        role: "soc_analyst",
        jurisdiction: "Dubai & UAE",
        timestamp: new Date().toISOString(),
      });
    }

    // 2. Forward to backend FastAPI /api/v1/threats/auth/verify endpoint
    try {
      const res = await fetch(`${API_BASE}/api/v1/threats/auth/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": passkey,
        },
        body: JSON.stringify({ passkey }),
      });

      if (res.ok) {
        const data = await res.json();
        return NextResponse.json({
          status: "authenticated",
          authenticated: Boolean(data.authenticated),
          role: data.role || "soc_analyst",
          jurisdiction: data.jurisdiction || "Dubai & UAE",
          timestamp: data.timestamp || new Date().toISOString(),
        });
      }
    } catch (backendErr) {
      console.warn("Backend auth verification proxy failed or timed out:", backendErr);
    }

    return NextResponse.json(
      { authenticated: false, detail: "Invalid security clearance passkey. Access denied." },
      { status: 403 }
    );
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { authenticated: false, detail: `Authentication error: ${msg}` },
      { status: 500 }
    );
  }
}
