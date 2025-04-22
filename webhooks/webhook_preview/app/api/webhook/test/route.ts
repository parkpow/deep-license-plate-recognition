import { type NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const data = await request.json();

    return NextResponse.json({
      success: true,
      message: "Test endpoint working correctly",
      receivedData: data,
    });
  } catch (error) {
    console.error("Error in test endpoint:", error);
    return NextResponse.json(
      { error: "Failed to process test request" },
      { status: 400 },
    );
  }
}

export async function GET() {
  return NextResponse.json({
    success: true,
    message: "Test endpoint working correctly",
  });
}
