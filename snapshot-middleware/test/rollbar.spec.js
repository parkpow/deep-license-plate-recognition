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
    const events = [];
    const ctx = createExecutionContext();
    const response = await worker.tail(events, env, ctx);
    await waitOnExecutionContext(ctx);
    expect(response).toBe(400);
  });
});
