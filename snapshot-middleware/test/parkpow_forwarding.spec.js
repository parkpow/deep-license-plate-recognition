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

describe("ParkPow Forwarding", () => {
  /**
   * Normal Forwarding of unchanged ParkPow response by sending `?parkpow_forwarding=1`
   */
  it("Forwards Normal(non-empty results) Snapshot Response", async () => {
    fetchMock
      .get(SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponse);

    fetchMock
      .get(PARKPOW_BASE_URL)
      .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
      .reply(200, SurvisionParkPowResponse);

    const url = WORKER_REQUEST_INPUT + "?parkpow_forwarding=1";
    const req = createJsonUploadRequest(
      url,
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(200);
    expect(await response.json()).toStrictEqual(SurvisionParkPowResponse);
  });

  it("Forwards only the first Snapshot result if multiple", async () => {
    fetchMock
      .get(SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponseX2);

    fetchMock
      .get(PARKPOW_BASE_URL)
      .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
      .reply(200, SurvisionParkPowResponse);

    const url = WORKER_REQUEST_INPUT + "?parkpow_forwarding=1";
    const req = createJsonUploadRequest(
      url,
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(200);
    expect(await response.json()).toStrictEqual(SurvisionParkPowResponse);
  });

  it("Fallback to Camera results if Snapshot is empty.", async () => {
    fetchMock
      .get(SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, GenetecSnapshotResponse);

    fetchMock
      .get(PARKPOW_BASE_URL)
      .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
      .reply(200, GenetecResultParkPow);

    const url = WORKER_REQUEST_INPUT + "?parkpow_forwarding=1";

    const req = createJsonUploadRequest(url, GenetecSamplePayload, {});
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(200);
    expect(await response.json()).toStrictEqual(GenetecResultParkPow);
  });

  it("Retries Rate Limits", async () => {
    const rateLimitResponse = {
      detail: "Error Message",
      status_code: 429,
    };
    fetchMock
      .get(SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponse);

    fetchMock
      .get(PARKPOW_BASE_URL)
      .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
      .reply(429, JSON.stringify(rateLimitResponse))
      .times(3);

    let url = WORKER_REQUEST_INPUT + "?parkpow_forwarding=1";
    let req = createJsonUploadRequest(
      url,
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(429);
    expect(await response.json()).toStrictEqual(rateLimitResponse);
  });
});
