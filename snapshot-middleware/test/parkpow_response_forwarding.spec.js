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
import SurvisionSnapshotResponse from "./assets/SurvisionSnapshot.json";
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

describe("ParkPow Response message and status is forwarded to worker response", async () => {
  const parkPowStatusCases = [
    [300, JSON.stringify({ detail: "Response 300" }), 1],
    [403, JSON.stringify({ detail: "Invalid token." }), 1],
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
  test.each(parkPowStatusCases)(
    "ParkPow Status: %s is forwarded as worker response",
    async (status, parkPowResponse, times) => {
      // const mockAgent = new MockAgent({ connections: 1 })
      // mockAgent.disableNetConnect();

      const client1 = fetchMock.get(import.meta.env.SNAPSHOT_BASE_URL);
      client1
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, SurvisionSnapshotResponse);

      const client2 = fetchMock.get(import.meta.env.PARKPOW_BASE_URL);
      client2
        .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
        .reply(status, parkPowResponse)
        .times(times);

      const url = WORKER_REQUEST_INPUT + "?parkpow_forwarding=1";
      let req = createJsonUploadRequest(
        url,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      ); // Create an empty context to pass to `worker.fetch()`
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(status);
      expect(await response.text()).toStrictEqual(parkPowResponse);
    },
  );
});
