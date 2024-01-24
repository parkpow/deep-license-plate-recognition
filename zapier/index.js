const hydrators = require("./hydrators");
const authentication = require("./authentication");
const createRecognition = require("./creates/createRecognition");

const addTokenToHeader = (request, z, bundle) => {
  request.headers.Authorization = `Token ${bundle.authData.token}`;
  return request;
};

const App = {
  // This is just shorthand to reference the installed dependencies you have.
  // Zapier will need to know these before we can upload.
  version: require("./package.json").version,
  platformVersion: require("zapier-platform-core").version,
  authentication,
  // beforeRequest & afterResponse are optional hooks into the provided HTTP client
  beforeRequest: [addTokenToHeader],
  afterResponse: [],
  // Any hydrators go here
  hydrators,
  resources: {},
  // If you want your trigger to show up, you better include it here!
  triggers: {},

  // If you want your searches to show up, you better include it here!
  searches: {},

  // If you want your creates to show up, you better include it here!
  creates: {
    [createRecognition.key]: createRecognition,
  },
};
module.exports = App;
