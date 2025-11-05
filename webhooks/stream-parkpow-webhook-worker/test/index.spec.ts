import { createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;
const requestPayload = JSON.stringify({ foo: "bar" });
const testEnv = {
  PARKPOW_ENDPOINT: "http://example.com/parkpow-webhook",
  PARKPOW_TOKEN: "parkpow-token-456",
  STREAM_TOKEN: "stream-token-123",
};

describe("Stream to ParkPow webhook worker", () => {
  it("should reject non-POST requests", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "GET",
    });

    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(401);
    expect(await response.text()).toBe("Unauthorized");
  });

  it("should forward POST request with correct incoming Authorization header and multipart/form-data body with mock image as-is", async () => {
    const boundary = "37dd8504ce9387f0e07b86f03a25ab0a"; // pragma: allowlist secret
    const imageBuffer = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);

    const encoder = new TextEncoder();
    const CRLF = "\r\n";
    const bodyParts: (string | Uint8Array)[] = [
      `--${boundary}${CRLF}` +
        `Content-Disposition: form-data; name="json"${CRLF}` +
        `Content-Type: application/json${CRLF}${CRLF}` +
        `{"foo":"bar"}${CRLF}` +
        `--${boundary}${CRLF}` +
        `Content-Disposition: form-data; name="upload"; filename="taxi.jpg"${CRLF}` +
        `Content-Type: image/jpeg${CRLF}${CRLF}`,
      imageBuffer,
      `${CRLF}--${boundary}--${CRLF}`,
    ];

    function concatUint8Arrays(arrays: Uint8Array[]): Uint8Array {
      const totalLength = arrays.reduce(
        (acc: number, curr: Uint8Array) => acc + curr.length,
        0,
      );
      const result = new Uint8Array(totalLength);
      let offset = 0;
      for (const arr of arrays) {
        result.set(arr, offset);
        offset += arr.length;
      }
      return result;
    }
    const encodedParts: Uint8Array[] = bodyParts.map((part) =>
      typeof part === "string" ? encoder.encode(part) : part,
    );
    const multipartBody: Uint8Array = concatUint8Arrays(encodedParts);

    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": `multipart/form-data; boundary=${boundary}`,
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: multipartBody,
    });

    const ctx = createExecutionContext();
    const originalFetch = globalThis.fetch;
    let capturedRequest: Request | undefined;
    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      capturedRequest = new Request(input as string, init);
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    globalThis.fetch = originalFetch;

    expect(response.status).toBe(200);
    expect(capturedRequest).toBeDefined();
    if (capturedRequest) {
      expect(capturedRequest.headers.get("Authorization")).toBe(
        `Token ${testEnv.PARKPOW_TOKEN}`,
      );
      expect(capturedRequest.headers.get("Content-Type")).toBe(
        `multipart/form-data; boundary=${boundary}`,
      );
      const forwardedBody = new Uint8Array(await capturedRequest.arrayBuffer());
      expect(forwardedBody.length).toBe(multipartBody.length);
      expect(forwardedBody.every((v, i) => v === multipartBody[i])).toBe(true);
    }
  });

  it("should reject POST request with missing Authorization header", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: requestPayload,
    });
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(401);
    expect(await response.text()).toBe("Unauthorized");
  });

  it("should reject POST request with invalid Authorization header", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Token wrong-token",
      },
      body: requestPayload,
    });
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(401);
    expect(await response.text()).toBe("Unauthorized");
  });

  it("should handle fetch errors gracefully", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: requestPayload,
    });
    const ctx = createExecutionContext();
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      throw new Error("Network error");
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    globalThis.fetch = originalFetch;

    expect(response.status).toBe(502);
    expect(await response.text()).toBe("Network error");
  });

  it("should preserve ParkPow response status and headers", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: requestPayload,
    });

    const ctx = createExecutionContext();
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      return new Response(JSON.stringify({ error: "Bad request" }), {
        status: 400,
        statusText: "Bad Request",
        headers: { "X-Custom-Header": "test-value" },
      });
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    globalThis.fetch = originalFetch;

    expect(response.status).toBe(400);
    expect(response.statusText).toBe("Bad Request");
    expect(response.headers.get("X-Custom-Header")).toBe("test-value");
  });

  it("should handle missing PARKPOW_TOKEN", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: requestPayload,
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
      capturedRequest = new Request(input as string, init);
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
      });
    };

    const response = await worker.fetch(request, envWithoutToken, ctx);
    await waitOnExecutionContext(ctx);
    globalThis.fetch = originalFetch;

    expect(response.status).toBe(400);
    expect(capturedRequest).toBeUndefined();
  });

  it("should handle ParkPow 401 Unauthorized response", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: requestPayload,
    });

    const ctx = createExecutionContext();
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      return new Response(JSON.stringify({ detail: "Invalid token" }), {
        status: 401,
        statusText: "Unauthorized",
      });
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    globalThis.fetch = originalFetch;

    expect(response.status).toBe(401);
  });

  it("should handle ParkPow 403 Forbidden response", async () => {
    const request = new IncomingRequest("http://example.com/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${testEnv.STREAM_TOKEN}`,
      },
      body: requestPayload,
    });

    const ctx = createExecutionContext();
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify({ detail: "Token not authorized for this resource" }),
        {
          status: 403,
          statusText: "Forbidden",
        },
      );
    };

    const response = await worker.fetch(request, testEnv, ctx);
    await waitOnExecutionContext(ctx);
    globalThis.fetch = originalFetch;

    expect(response.status).toBe(403);
  });
});
