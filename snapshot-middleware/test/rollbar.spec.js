// import {
//   env,
//   createExecutionContext,
//   waitOnExecutionContext,
//   SELF,
// } from "cloudflare:test";
import { describe, it, expect } from "vitest";

describe("Error Logging to RollBar", () => {
  it("Exception is captured", async () => {
    throw new Error("Not Implemented");
  });
});
