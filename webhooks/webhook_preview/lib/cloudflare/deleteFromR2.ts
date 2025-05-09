import { DeleteObjectsCommand, S3Client } from "@aws-sdk/client-s3";

const s3Client = new S3Client({
  region: "auto",
  endpoint: `https://${process.env.CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: {
    accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_ACCESS_KEY!,
  },
});

export async function deleteFromR2(keys: string[]) {
  if (keys.length === 0) return;

  const command = new DeleteObjectsCommand({
    Bucket: process.env.CLOUDFLARE_R2_BUCKET_NAME!,
    Delete: {
      Objects: keys.map((key) => ({ Key: key })),
      Quiet: false,
    },
  });

  const response = await s3Client.send(command);
  return response;
}
