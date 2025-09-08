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
  it,
  test,
  vi,
} from "vitest";

import worker from "../src/index";

import SurvisionSamplePayload from "./assets/Survision.json";
import SurvisionSnapshotResponse from "./assets/SurvisionSnapshot.json";
import SurvisionParkPowResponse from "./assets/SurvisionParkPow.json";

import {
  WORKER_REQUEST_INPUT,
  SURVISION_HEADERS_DEFAULT,
  createJsonUploadRequest,
} from "./utils";
import { validInt } from "../src/utils.js";

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
  const workerParams = [
    // param, value
    [null, null],
    ["parkpow_forwarding", 1],
  ];
  test.each(workerParams)(
    "Respond with Snapshot Response Always: %s => %s",
    async (param, value) => {
      fetchMock
        .get(import.meta.env.SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, SurvisionSnapshotResponse);

      let url;
      if (param && value) {
        url = `${WORKER_REQUEST_INPUT}?${param}=${value}`;

        fetchMock
          .get(import.meta.env.PARKPOW_BASE_URL)
          .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
          .reply(200, SurvisionParkPowResponse);
      } else {
        url = WORKER_REQUEST_INPUT;
      }

      const req = createJsonUploadRequest(
        url,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      );
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      await waitOnExecutionContext(ctx);
      expect(response.status).toBe(200);
      expect(await response.json()).toStrictEqual(SurvisionSnapshotResponse);
    },
  );

  it("Retries ParkPow Rate Limits", async () => {
    fetchMock
      .get(import.meta.env.SNAPSHOT_BASE_URL)
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSnapshotResponse);

    fetchMock
      .get(import.meta.env.PARKPOW_BASE_URL)
      .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
      .reply(429, JSON.stringify({}))
      .times(validInt(import.meta.env.PARKPOW_RETRY_LIMIT, 5));

    let url = WORKER_REQUEST_INPUT + "?parkpow_forwarding=1";
    let req = createJsonUploadRequest(
      url,
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    await waitOnExecutionContext(ctx);
    expect(response.status).toBe(200);

    // If not retry happens upto PARKPOW_RETRY_LIMIT there will be an error from interceptor
    // UndiciError: 1 interceptor is pending:
  });
});
