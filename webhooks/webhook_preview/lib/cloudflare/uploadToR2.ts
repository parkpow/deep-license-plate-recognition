// lib/cloudflare/uploadToR2.ts
import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { randomUUID } from "crypto";

const s3Client = new S3Client({
  region: "auto",
  endpoint: `https://${process.env.CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: {
    accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_ACCESS_KEY!,
  },
});

export async function uploadToR2(file: File, prefix = "uploads") {
  const buffer = Buffer.from(await file.arrayBuffer());
  const extension = file.name.split(".").pop() || "bin";
  const key = `${prefix}/${randomUUID()}.${extension}`;

  const command = new PutObjectCommand({
    Bucket: process.env.CLOUDFLARE_R2_BUCKET_NAME!,
    Key: key,
    Body: buffer,
    ContentType: file.type,
  });

  const test = await s3Client.send(command);

  return {
    url: `https://${process.env.CLOUDFLARE_R2_PUBLIC_DOMAIN}/${key}`,
    key,
  };
}
