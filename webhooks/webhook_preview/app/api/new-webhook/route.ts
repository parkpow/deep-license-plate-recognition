import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { uuid } = body;

    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    if (!uuid || !uuidRegex.test(uuid)) {
      return NextResponse.json(
        { success: false, message: "Invalid UUID" },
        { status: 400 },
      );
    }

    let webhook = await prisma.webhook.findUnique({
      where: { uuid },
    });

    if (!webhook) {
      webhook = await prisma.webhook.create({
        data: { uuid },
      });
    }

    return NextResponse.json(
      { success: true, message: "Webhook created" },
      { status: 201 },
    );
  } catch (error) {
    console.error("Webhook creation error:", error);
    return NextResponse.json(
      { success: false, message: "Internal Server Error" },
      { status: 500 },
    );
  }
}
