import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
  fetchMock,
} from "cloudflare:test";
import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
  MockInstance,
  test,
} from "vitest";

import worker from "../src/index";

import GenetecSamplePayload from "./Genetec.json";
import GenetecSnapshotResponse from "./GenetecSnapshot.json";
import GenetecResultParkPow from "./GenetecResultParkPow.json";
import SurvisionSamplePayload from "./Survision.json";
import SurvisionSnapshotResponse from "./SurvisionSnapshot.json";
import SurvisionSnapshotResponseX2 from "./SurvisionSnapshotX2.json";
import SurvisionParkPowResponse from "./SurvisionParkPow.json";
import { isMockActive, MockAgent, setDispatcher } from "cloudflare:mock-agent";
import { validInt } from "../src/utils";
import { PROCESSOR_GENETEC } from "../src/cameras";

const WORKER_REQUEST_INPUT = "http://snapshot-middleware.platerecognizer.com";
const SURVISION_HEADERS_DEFAULT = {
  "survision-serial-number": "sv1-searial-1",
};

const SNAPSHOT_BASE_URL = "https://api.platerecognizer.com";
// const PARKPOW_BASE_URL = "https://app.parkpow.com";
const PARKPOW_BASE_URL = "http://0.0.0.0:8000";

beforeAll(() => {
  // throw errors if an outbound request isn't mocked
  fetchMock.disableNetConnect();
});

beforeEach(() => fetchMock.activate());

afterEach(() => {
  fetchMock.assertNoPendingInterceptors();
  fetchMock.deactivate();
});

/**
 * Create Expected Request from cameras with relevant headers and payload
 * @param input
 * @param jsonData
 * @param extraHeaders
 * @returns {Request}
 */
function createJsonUploadRequest(input, jsonData, extraHeaders = {}) {
  const bodyJson = JSON.stringify(jsonData);
  return new Request(input, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "content-length": bodyJson.length,
      ...extraHeaders,
    },
    body: bodyJson,
  });
}

describe("forwards snapshot response to user as worker response", async () => {
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
        .get(SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(status, mockSnapshotResponse)
        .times(times);

      let req = createJsonUploadRequest(
        WORKER_REQUEST_INPUT,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      ); // Create an empty context to pass to `worker.fetch()`
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(status);
      // By default, the response should be Snapshot response
      //  unless manually forwarded to ParkPow then it's ParkPow response
      expect(await response.text()).toStrictEqual(mockSnapshotResponse);
    },
  );
});
