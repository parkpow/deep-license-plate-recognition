import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.toml" },
        main: "./src/index.js",
        // singleWorker: true,
        miniflare: {
          bindings: {
            PARKPOW_TOKEN: "empty",
            //PARKPOW_URL: 'http://0.0.0.0:8000',
            PARKPOW_URL: "",
            SNAPSHOT_TOKEN: "empty",
            SNAPSHOT_URL: "",
            ROLLBAR_TOKEN: "empty",
            RETRY_DELAY: 0,
            PARKPOW_RETRY_LIMIT: 2,
            SNAPSHOT_RETRY_LIMIT: 2,
          },
        },
      },
    },
    env: {
      SNAPSHOT_BASE_URL: "https://api.platerecognizer.com",
      PARKPOW_BASE_URL: "https://app.parkpow.com",
      // PARKPOW_BASE_URL: "http://0.0.0.0:8000"
    },
    coverage: {
      reporter: ["text", "json", "html"],
      provider: "istanbul", // or 'v8'
    },
  },
});
