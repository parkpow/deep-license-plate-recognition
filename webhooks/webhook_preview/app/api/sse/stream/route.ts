import { NextRequest } from "next/server";
import { addClient, removeClient } from "@/lib/sse-store";
import { randomUUID } from "crypto";

export async function GET(req: NextRequest) {
  const uuid = req.nextUrl.searchParams.get("uuid");
  if (!uuid) return new Response("UUID não informado", { status: 400 });

  const encoder = new TextEncoder();
  const stream = new TransformStream();
  const writer = stream.writable.getWriter();
  const id = randomUUID();

  addClient(uuid, {
    id,
    res: {
      write: (data: string) => writer.write(encoder.encode(data)),
    },
  });

  writer.write(encoder.encode("event: connected\ndata: ok\n\n"));

  req.signal.addEventListener("abort", () => {
    removeClient(uuid, id);
  });

  return new Response(stream.readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
