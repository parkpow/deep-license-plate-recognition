import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
  fetchMock,
} from "cloudflare:test";
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  test,
} from "vitest";

import worker from "../src/index";

import SurvisionSamplePayload from "./assets/Survision.json";
import {
  WORKER_REQUEST_INPUT,
  SURVISION_HEADERS_DEFAULT,
  createJsonUploadRequest,
} from "./utils";

beforeAll(() => {
  // throw errors if an outbound request isn't mocked
  fetchMock.disableNetConnect();
});

beforeEach(() => fetchMock.activate());

afterEach(() => {
  fetchMock.assertNoPendingInterceptors();
  fetchMock.deactivate();
});

describe("Forwards snapshot response to user as worker response", async () => {
  const snapshotStatusCases = [
    [300, JSON.stringify({ detail: "Response 300" }), 1],
    [400, JSON.stringify({ detail: "Response 400" }), 1],
    [
      429,
      JSON.stringify({
        detail: "Request was throttled. Expected available in 1 second.",
        status_code: 429,
      }),
      3,
    ],
    [500, JSON.stringify({ detail: "Response 500" }), 3],
    [504, '<doc type="html">...', 3],
  ];
  test.each(snapshotStatusCases)(
    "Snapshot Status: %s is forwarded as worker response",
    async (status, mockSnapshotResponse, times) => {
      fetchMock
        .get(import.meta.env.SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(status, mockSnapshotResponse)
        .times(times);

      const req = createJsonUploadRequest(
        WORKER_REQUEST_INPUT,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      );
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(status);
      expect(await response.text()).toStrictEqual(mockSnapshotResponse);
    },
  );
});
