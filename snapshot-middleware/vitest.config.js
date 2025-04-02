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
          },
        },
      },
    },
  },
});
