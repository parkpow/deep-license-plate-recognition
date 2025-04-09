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

const rollbarPayload = {
  data: {
    environment: "production",
    body: {
      telemetry: [
        {
          level: "log",
          timestamp_ms: 1587058642005,
          source: "server",
          type: "log",
          body: {
            message: "string passed to console.log()",
          },
        },
      ],
      trace_chain: [
        {
          frames: [
            {
              filename: "index.js",
              lineno: null,
              colno: null,
              method: null,
              args: null,
            },
          ],
          exception: {
            class: "Error",
            message: "rollbar-error-handler",
            description: "Threw a sample exception",
          },
        },
      ],
    },
    timestamp: 1587058642005,
    code_version: "TestId",
    language: "javascript",
    request: {
      url: "https://example.com/some/requested/url",
      method: "GET",
      headers: {
        "cf-ray": "57d55f210d7b95f3",
        "x-custom-header-name": "my-header-value",
      },
      params: {
        colo: "SJC",
      },
    },
  },
};

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
        scriptVersion: {
          id: "TestId",
        },
      },
    ];
    fetchMock
      .get("https://api.rollbar.com")
      .intercept({ path: "/api/1/item/", method: "POST" })
      .reply(200, ({ body }) => {
        // throw new Error(body)
        expect(JSON.parse(body)).toStrictEqual(rollbarPayload);
        return body;
      });

    const ctx = createExecutionContext();
    await worker.tail(events, env, ctx);
    await waitOnExecutionContext(ctx);
  });
});
