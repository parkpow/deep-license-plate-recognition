import { createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("Stream to ParkPow webhook worker", () => {
  let testEnv: {
    PARKPOW_ENDPOINT: string;
    PARKPOW_TOKEN: string;
    STREAM_TOKEN: string;
  };

  beforeEach(() => {
    testEnv = {
      PARKPOW_ENDPOINT: "https://app.parkpow.com/api/v1/webhook-receiver/",
      PARKPOW_TOKEN: "parkpow-token-123",
      STREAM_TOKEN: "stream-token-456",
    };
  });

  it("should reject non-POST requests", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "GET",
    });
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(405);
    expect(await response.text()).toBe("Method not allowed");
  });

  it("should forward POST request with correct incoming Authorization header", async () => {
    const testPayload = {
      uid: "test-stream-id",
      timestamp: Date.now(),
      data: { test: "data" },
    };

    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: JSON.stringify(testPayload),
    });

    const ctx = createExecutionContext();
    const originalFetch = globalThis.fetch;
    let capturedRequest: Request | undefined;

    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      if (typeof input === "string" || input instanceof URL) {
        const url = input.toString();
        if (url === testEnv.PARKPOW_ENDPOINT) {
          capturedRequest = new Request(url, init);
          return new Response(JSON.stringify({ success: true }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
      } else if (input instanceof Request) {
        if (input.url === testEnv.PARKPOW_ENDPOINT) {
          capturedRequest = input;
          return new Response(JSON.stringify({ success: true }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
      }
      return originalFetch(input, init);
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    globalThis.fetch = originalFetch;

    expect(response.status).toBe(200);
    expect(capturedRequest).not.toBeNull();

    if (capturedRequest) {
      expect(capturedRequest.headers.get("Authorization")).toBe(
        `Token ${testEnv.PARKPOW_TOKEN}`,
      );
      expect(capturedRequest.headers.get("Content-Type")).toBe("application/json");

      const forwardedBody = await capturedRequest.json();
      expect(forwardedBody).toEqual(testPayload);
    }
  });

  it("should reject POST request with missing Authorization header", async () => {
    const testPayload = { test: "data" };
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(testPayload),
    });
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    expect(response.status).toBe(401);
    expect(await response.text()).toBe("Unauthorized");
  });

  it("should reject POST request with invalid Authorization header", async () => {
    const testPayload = { test: "data" };
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Token wrong-token",
      },
      body: JSON.stringify(testPayload),
    });
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    expect(response.status).toBe(401);
    expect(await response.text()).toBe("Unauthorized");
  });

  it("should handle fetch errors gracefully", async () => {
    const testPayload = { test: "data" };

    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: JSON.stringify(testPayload),
    });

    const ctx = createExecutionContext();

    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      throw new Error("Network error");
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    globalThis.fetch = originalFetch;

    expect(response.status).toBe(500);
    expect(await response.text()).toBe("Internal server error");
  });

  it("should handle invalid JSON payload", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: "invalid json",
    });

    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(500);
    expect(await response.text()).toBe("Internal server error");
  });

  it("should preserve ParkPow response status and headers", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: JSON.stringify({ test: "data" }),
    });

    const ctx = createExecutionContext();

    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input: RequestInfo | URL) => {
      if (
        (typeof input === "string" || input instanceof URL
          ? input.toString()
          : input instanceof Request
            ? input.url
            : "") === testEnv.PARKPOW_ENDPOINT
      ) {
        return new Response(JSON.stringify({ error: "Bad request" }), {
          status: 400,
          statusText: "Bad Request",
          headers: { "X-Custom-Header": "test-value" },
        });
      }
      return originalFetch(input);
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    globalThis.fetch = originalFetch;

    expect(response.status).toBe(400);
    expect(response.statusText).toBe("Bad Request");
    expect(response.headers.get("X-Custom-Header")).toBe("test-value");
  });

  it("should handle missing PARKPOW_TOKEN", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: JSON.stringify({ test: "data" }),
    });

    const ctx = createExecutionContext();
    const envWithoutToken = {
      PARKPOW_ENDPOINT: testEnv.PARKPOW_ENDPOINT,
      PARKPOW_TOKEN: "",
      STREAM_TOKEN: testEnv.STREAM_TOKEN,
    };

    const originalFetch = globalThis.fetch;
    let capturedRequest: Request | undefined;

    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      if (typeof input === "string" || input instanceof URL) {
        const url = input.toString();
        if (url === testEnv.PARKPOW_ENDPOINT) {
          capturedRequest = new Request(url, init);
          return new Response(JSON.stringify({ success: true }), {
            status: 200,
          });
        }
      } else if (input instanceof Request) {
        if (input.url === testEnv.PARKPOW_ENDPOINT) {
          capturedRequest = input;
          return new Response(JSON.stringify({ success: true }), {
            status: 200,
          });
        }
      }
      return originalFetch(input, init);
    };

    const response = await worker.fetch(request, envWithoutToken, ctx);
    await waitOnExecutionContext(ctx);

    globalThis.fetch = originalFetch;

    expect(response.status).toBe(200);
    expect(capturedRequest).not.toBeNull();
    if (capturedRequest) {
      expect(capturedRequest.headers.get("Authorization")).toBe("Token");
    }
  });

  it("should handle ParkPow 401 Unauthorized response", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: JSON.stringify({ test: "data" }),
    });

    const ctx = createExecutionContext();

    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input: RequestInfo | URL) => {
      if (
        (typeof input === "string" || input instanceof URL
          ? input.toString()
          : input instanceof Request
            ? input.url
            : "") === testEnv.PARKPOW_ENDPOINT
      ) {
        return new Response(JSON.stringify({ detail: "Invalid token" }), {
          status: 401,
          statusText: "Unauthorized",
        });
      }
      return originalFetch(input);
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    globalThis.fetch = originalFetch;

    expect(response.status).toBe(401);
    expect(response.statusText).toBe("Unauthorized");
    const body = await response.json();
    expect(body).toEqual({ detail: "Invalid token" });
  });

  it("should handle ParkPow 403 Forbidden response", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: JSON.stringify({ test: "data" }),
    });

    const ctx = createExecutionContext();

    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input: RequestInfo | URL) => {
      if (
        (typeof input === "string" || input instanceof URL
          ? input.toString()
          : input instanceof Request
            ? input.url
            : "") === testEnv.PARKPOW_ENDPOINT
      ) {
        return new Response(
          JSON.stringify({ detail: "Token not authorized for this resource" }),
          {
            status: 403,
            statusText: "Forbidden",
          },
        );
      }
      return originalFetch(input);
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    globalThis.fetch = originalFetch;

    expect(response.status).toBe(403);
    expect(response.statusText).toBe("Forbidden");
    const body = await response.json();

    expect(body).toEqual({ detail: "Token not authorized for this resource" });
  });
});
