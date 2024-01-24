/* globals describe, expect, test */

const zapier = require("zapier-platform-core");

const App = require("../");
const appTester = zapier.createAppTester(App);
zapier.tools.env.inject();

const CORE_VERSION = zapier.version.split(".").map((s) => parseInt(s));

const FILE_URL = "https://app.platerecognizer.com/static/demo.jpg";

// This is what you get when doing `curl <FILE_URL> | sha1sum`
const EXPECTED_SHA1 = "3cf58b42a0fb1b7cc58de8110096841ece967530";

describe("createRecognition", () => {
  test("upload file", async () => {
    if (CORE_VERSION[0] < 10) {
      console.warn(
        `skipped because this only works on core v10+ and you're on ${zapier.version}`,
      );
      return;
    }

    const bundle = {
      inputData: {
        upload_url: FILE_URL,
      },
    };
    // const result = await appTester(
    //     App.creates.createRecognition.operation.perform,
    //     bundle
    // );
    // expect(result.upload.sha1).toBe(EXPECTED_SHA1);
  });
});
