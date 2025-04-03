import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
  fetchMock,
} from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";

import worker from "../src/index";

import GenetecSamplePayload from "./Genetec.json";
import GenetecSnapshotResponse from "./GenetecSnapshot.json";
import GenetecResultParkPow from "./GenetecResultParkPow.json";
import SurvisionSamplePayload from "./Survision.json";
import SurvisionSnapshotResponse from "./SurvisionSnapshot.json";
import SurvisionSnapshotResponseX2 from "./SurvisionSnapshotX2.json";
import SurvisionParkPowResponse from "./SurvisionParkPow.json";

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

describe("ParkPow Forwarding", () => {
  /**
   * Normal Forwarding of unchanged ParkPow response by sending `?parkpow_forwarding=1`
   */
  it("Forwards Normal(non-empty results) Snapshot Response", async () => {
    fetchMock
      .get(import.meta.env.SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponse);

    fetchMock
      .get(import.meta.env.PARKPOW_BASE_URL)
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
      .get(import.meta.env.SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponseX2);

    fetchMock
      .get(import.meta.env.PARKPOW_BASE_URL)
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
      .get(import.meta.env.SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, GenetecSnapshotResponse);

    fetchMock
      .get(import.meta.env.PARKPOW_BASE_URL)
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
      .get(import.meta.env.SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponse);

    fetchMock
      .get(import.meta.env.PARKPOW_BASE_URL)
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
