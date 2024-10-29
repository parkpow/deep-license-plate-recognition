import { fetchWithRetry } from "./utils";
import ErrorStackParser from "error-stack-parser";

const rollbarUrl = `https://api.rollbar.com/api/1/item/`;

const Frame = ({ fileName, lineNumber, columnNumber, functionName, args }) => {
  const data = {};
  data.filename = fileName;
  data.lineno = lineNumber;
  data.colno = columnNumber;
  data.method = functionName;
  data.args = args;
  return data;
};

class Rollbar {
  constructor(token, environment) {
    if (!token) {
      throw new Error("Token is required for Rollbar initialization");
    }
    this.token = token;
    this.environment = environment != null ? environment : "production";
  }

  createTrace(description, exception) {
    let stackFrames = null;
    try {
      const stack = ErrorStackParser.parse(exception);
      stackFrames = stack.map((stackFrame) => Frame(stackFrame));
    } catch (e) {
      stackFrames = [
        Frame({
          fileName: "index.js",
          lineNumber: null,
          columnNumber: null,
          functionName: null,
          args: null,
        }),
      ];
    }
    return {
      frames: stackFrames,
      exception: {
        class: exception.name,
        message: exception.message,
        description: description,
      },
    };
  }

  createTelemetry(eventLog) {
    return {
      level: eventLog["level"],
      timestamp_ms: eventLog["timestamp"],
      source: "server",
      type: "log",
      body: {
        message: eventLog["message"][0],
      },
    };
  }

  error(exceptions, description, timestamp, event, eventLogs, codeVersion) {
    const traceChain = exceptions.map((exception) =>
      this.createTrace(description, exception),
    );
    const telemetry = eventLogs.map((eventLog) =>
      this.createTelemetry(eventLog),
    );
    const rollbarData = {
      environment: this.environment,
      body: { telemetry: telemetry, trace_chain: traceChain },
      timestamp: timestamp,
      code_version: codeVersion,
      language: "javascript",
    };

    if ("request" in event) {
      const request = event["request"];
      const params = request["cf"];
      delete params["tlsClientAuth"];
      delete params["tlsExportedAuthenticator"];
      rollbarData["request"] = {
        url: request["url"],
        method: request["method"],
        headers: request["headers"],
        params: params,
      };
    }

    let init = {
      method: "POST",
      body: JSON.stringify({ data: rollbarData }),
      headers: {
        "Content-type": "application/json",
        "X-Rollbar-Access-Token": this.token,
      },
    };
    return fetchWithRetry(rollbarUrl, init).then((response) => response.json());
  }
}

export default {
  async tail(events, env, ctx) {
    const rollbar = new Rollbar(env.ROLLBAR_TOKEN, "production");
    for (const event of events) {
      if (event.exceptions.length) {
        ctx.waitUntil(
          rollbar.error(
            event.exceptions,
            event["scriptName"],
            event["eventTimestamp"],
            event["event"],
            event["logs"],
            event["scriptVersion"]["id"],
          ),
        );
      }
    }
  },
};
