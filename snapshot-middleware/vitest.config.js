import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.toml" },
        main: "./src/index.js",
        miniflare: {
          bindings: {
            PARKPOW_TOKEN: "empty",
            SNAPSHOT_TOKEN: "empty",
            ROLLBAR_TOKEN: "empty",
            RETRY_DELAY: 10,
            PARKPOW_RETRY_LIMIT: 2,
            SNAPSHOT_RETRY_LIMIT: 2,
          },
        },
      },
    },
  },
});
