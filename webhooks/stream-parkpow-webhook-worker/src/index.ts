import type { Context } from "hono";
import { Hono } from "hono";
import type { StatusCode } from "hono/utils/http-status";

const app = new Hono();

// Worker auth. middleware (Stream token)
app.use(async (c: Context, next: () => Promise<void>) => {
  const auth = c.req.header("Authorization");
  if (auth !== `Token ${c.env.STREAM_TOKEN}` || c.req.method !== "POST")
    return c.text("Unauthorized", 401);
  await next();
});

app.post("/", async (c: Context) => {
  if (!c.env.PARKPOW_TOKEN) return c.text("Proxy missing parkpow credentials", 400);

  // Update authorization header for ParkPow
  const incomingHeaders = new Headers(c.req.raw.headers);
  incomingHeaders.set("Authorization", `Token ${c.env.PARKPOW_TOKEN}`);

  try {
    // Forward request to ParkPow
    const resp = await fetch(c.env.PARKPOW_ENDPOINT, {
      method: c.req.method,
      headers: incomingHeaders,
      body: c.req.raw.body,
    });

    // Stream response from ParkPow
    return new Response(resp.body, resp);
  } catch (err) {
    return c.text(err instanceof Error ? err.message : "Unknown error", 502);
  }
});

export default app;
