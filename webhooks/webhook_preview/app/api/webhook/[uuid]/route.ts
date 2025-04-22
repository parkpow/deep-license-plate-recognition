import { deleteFromR2 } from "@/lib/cloudflare/deleteFromR2";
import { uploadToR2 } from "@/lib/cloudflare/uploadToR2";
import { findImageKeysByWebhookUUID } from "@/lib/image-to-remove";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Get the maximum number of webhook requests from environment variable or default to 50
const MAX_WEBHOOK_REQUESTS = Number.parseInt(
  process.env.NEXT_PUBLIC_MAX_WEBHOOK_REQUESTS || "50",
  10,
);

export async function POST(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const uuid = url.pathname.split("/").pop()!;

    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(uuid)) {
      return NextResponse.json(
        { error: "Invalid UUID format" },
        { status: 400 },
      );
    }

    const webhook = await prisma.webhook.findUnique({
      where: { uuid },
      select: {
        id: true,
        _count: {
          select: { requests: true },
        },
      },
    });

    if (!webhook) {
      return NextResponse.json({ error: "Webhook not found" }, { status: 404 });
    }

    if (webhook._count.requests >= MAX_WEBHOOK_REQUESTS) {
      return NextResponse.json(
        { error: "Request limit reached for this webhook" },
        { status: 429 },
      );
    }

    const contentType = request.headers.get("content-type") || "";
    let data: any;
    let imageUrl: string | undefined;

    if (contentType.includes("application/json")) {
      data = await request.json();
    } else if (contentType.includes("text")) {
      data = await request.text();
    } else if (contentType.includes("form")) {
      const formData = await request.formData();
      const rawData = formData.get("json");
      const imageFile = formData.get("upload");

      data = rawData ? JSON.parse(rawData.toString()) : null;

      if (imageFile && imageFile instanceof File) {
        const uploadResult = await uploadToR2(imageFile, "webhooks");
        imageUrl = uploadResult.url;
      }
    } else {
      data = await request.text(); // fallback
    }

    // const webhook = await prisma.webhook.findUnique({ where: { uuid } });

    // if (!webhook) {
    //   return NextResponse.json({ error: "Webhook not found" }, { status: 404 });
    // }

    // // Verifica se já atingiu o limite
    // const currentCount = await prisma.webhookRequest.count({
    //   where: { webhookId: webhook.id },
    // });

    // if (currentCount >= MAX_WEBHOOK_REQUESTS) {
    //   return NextResponse.json(
    //     { error: "Request limit reached for this webhook" },
    //     { status: 429 },
    //   );
    // }

    const webhookItem = {
      ...data,
      receivedAt: new Date().toISOString(),
    };

    if (imageUrl) {
      await prisma.image.create({
        data: {
          url: imageUrl,
          webhookRequest: {
            create: {
              data: webhookItem,
              webhookId: webhook.id,
            },
          },
        },
      });
    } else {
      await prisma.webhookRequest.create({
        data: {
          data: webhookItem,
          webhookId: webhook.id,
        },
      });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error processing webhook:", error);
    return NextResponse.json(
      { error: "Failed to process webhook" },
      { status: 400 },
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const uuid = url.pathname.split("/").pop()!;

    // Validate UUID format
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(uuid)) {
      return NextResponse.json(
        { error: "Invalid UUID format" },
        { status: 400 },
      );
    }

    // Find webhook
    const webhook = await prisma.webhook.findUnique({
      where: { uuid },
      include: {
        requests: {
          orderBy: { receivedAt: "desc" },
          include: {
            image: {
              select: {
                url: true,
              },
            },
          },
        },
      },
    });

    if (!webhook) {
      return NextResponse.json({ error: "Webhook not found" }, { status: 404 });
    }

    // Map the requests to the expected format
    const webhookData = webhook.requests.map((request) => ({
      ...request.data,
      image: request.image,
    }));

    return NextResponse.json(webhookData);
  } catch (error) {
    console.error("Error in GET handler:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const uuid = url.pathname.split("/").pop()!;

    // Validate UUID format
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(uuid)) {
      return NextResponse.json(
        { error: "Invalid UUID format" },
        { status: 400 },
      );
    }

    // Find webhook
    const webhook = await prisma.webhook.findUnique({
      where: { uuid },
    });

    if (!webhook) {
      return NextResponse.json({ error: "Webhook not found" }, { status: 404 });
    }

    const keys = await findImageKeysByWebhookUUID(uuid);
    await deleteFromR2(keys);
    console.log(`Deleting images for webhook with UUID: ${keys}`);

    // Delete all requests for this webhook
    await prisma.webhookRequest
      .deleteMany({
        where: { webhookId: webhook.id },
      })
      .then(() => {
        console.log(
          `Deleted ${keys.length} images for webhook with UUID: ${keys}`,
        );
      });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error in DELETE handler:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
