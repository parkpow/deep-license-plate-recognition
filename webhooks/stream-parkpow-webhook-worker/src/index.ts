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

  // Clone headers except Authorization
  const incomingHeaders = new Headers();
  for (const [key, value] of c.req.raw.headers.entries())
    if (key.toLowerCase() !== "authorization") incomingHeaders.set(key, value);
  incomingHeaders.set("Authorization", `Token ${c.env.PARKPOW_TOKEN}`);

  try {
    // Forward request to ParkPow
    const resp = await fetch(c.env.PARKPOW_ENDPOINT, {
      method: c.req.method,
      headers: incomingHeaders,
      body: c.req.raw.body,
    });

    // Forward response from ParkPow
    const responseBody = await resp.text();
    const headersObj: Record<string, string> = {};
    for (const [key, value] of resp.headers.entries()) headersObj[key] = value;
    return c.newResponse(responseBody, resp.status as StatusCode, headersObj);
  } catch (err) {
    return c.text(err instanceof Error ? err.message : "Unknown error", 502);
  }
});

export default app;
