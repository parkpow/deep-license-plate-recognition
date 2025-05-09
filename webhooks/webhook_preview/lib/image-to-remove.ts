import { prisma } from "@/lib/prisma"; // adapte o caminho se necessário

export async function findImageKeysByWebhookUUID(
  uuid: string,
): Promise<string[]> {
  const webhookWithImages = await prisma.webhook.findUnique({
    where: { uuid },
    select: {
      requests: {
        select: {
          image: {
            select: {
              url: true,
            },
          },
        },
      },
    },
  });

  if (!webhookWithImages) return [];

  const urls = webhookWithImages.requests
    .map((req) => req.image?.url)
    .filter(Boolean) as string[];

  const baseURL = `https://${process.env.CLOUDFLARE_R2_PUBLIC_DOMAIN}/`;

  const keys = urls.map((url) => url.replace(baseURL, ""));

  return keys;
}
