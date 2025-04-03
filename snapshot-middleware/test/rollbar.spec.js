import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
  fetchMock,
} from "cloudflare:test";
import { describe, it, expect, beforeAll, beforeEach, afterEach } from "vitest";
import worker from "../src/rollbar";

beforeAll(() => {
  // throw errors if an outbound request isn't mocked
  fetchMock.disableNetConnect();
});
beforeEach(() => fetchMock.activate());
afterEach(() => {
  fetchMock.assertNoPendingInterceptors();
  fetchMock.deactivate();
});

describe("Error Logging to RollBar", () => {
  it("Exception is captured", async () => {
    const events = [
      {
        scriptName: "rollbar-error-handler",
        outcome: "exception",
        eventTimestamp: 1587058642005,
        event: {
          request: {
            url: "https://example.com/some/requested/url",
            method: "GET",
            headers: {
              "cf-ray": "57d55f210d7b95f3",
              "x-custom-header-name": "my-header-value",
            },
            cf: {
              colo: "SJC",
            },
          },
        },
        logs: [
          {
            message: ["string passed to console.log()"],
            level: "log",
            timestamp: 1587058642005,
          },
        ],
        exceptions: [
          {
            name: "Error",
            message: "Threw a sample exception",
            timestamp: 1587058642005,
          },
        ],
        diagnosticsChannelEvents: [
          {
            channel: "foo",
            message: "The diagnostic channel message",
            timestamp: 1587058642005,
          },
        ],
      },
    ];
    const ctx = createExecutionContext();
    const response = await worker.tail(events, env, ctx);
    await waitOnExecutionContext(ctx);
    expect(response).toBe(400);
  });
});
