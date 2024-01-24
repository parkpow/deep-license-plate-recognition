const getConnectionLabel = (z, bundle) => {
  // bundle.inputData will contain what the "test" URL (or function) returns
  // return bundle.inputData.username;
  return "Connected-user";
};

module.exports = {
  type: "custom",
  test: {
    // headers: {
    //     "Authorization": "Token {{bundle.authData.token}}"
    // },
    url: "https://api.platerecognizer.com/v1/plate-reader/",
  },
  fields: [
    {
      computed: false,
      key: "token",
      required: true,
      label: "Api Token",
      type: "string",
      helpText:
        "Go to your [Account Dashboard](https://app.platerecognizer.com/products/snapshot-cloud/) to find your API Key.",
    },
  ],
  connectionLabel: getConnectionLabel,
  customConfig: {},
};
