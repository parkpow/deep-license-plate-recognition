import { fetchWithRetry } from "./utils";
import ErrorStackParser from "error-stack-parser";

const rollbarUrl = `https://api.rollbar.com/api/1/item/`;

function Frame(stackFrame) {
	const data = {};
	data.filename = stackFrame.fileName;
	data.lineno = stackFrame.lineNumber;
	data.colno = stackFrame.columnNumber;
	data.method = stackFrame.functionName;
	data.args = stackFrame.args;
	return data;
}

var Rollbar = class {
	constructor(token, environment) {
		if (!token) {
			return;
		}
		this.token = token;
		this.environment = environment != null ? environment : "production";
	}

	createTrace(description, exception) {
		const stack = ErrorStackParser.parse(exception);
		return {
			frames: stack.map((stackFrame) => Frame(stackFrame)),
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
		const traceChain = [];
		for (const exception of exceptions) {
			traceChain.push(this.createTrace(description, exception));
		}

		const telemetry = [];
		for (const eventLog of eventLogs) {
			telemetry.push(this.createTelemetry(eventLog));
		}

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
};

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
