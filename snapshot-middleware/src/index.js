import { SnapshotApi } from "./snapshot";

function validGenetecEvent(data) {
	return (
		"CameraName" in data &&
		"ContextImage" in data &&
		"DateUtc" in data &&
		"TimeUtc" in data
	);
}

function validInt(i) {
	if (isNaN(i)) {
		throw new Error(`Invalid value for time - ${i}`);
	}
	return parseInt(i, 10);
}

function requestParams(request) {
	const { searchParams } = new URL(request.url);
	return {
		mmc: searchParams.get("mmc"),
		camera_id: searchParams.get("camera_id"),
		regions: searchParams.get("regions"),
		config: searchParams.get("config"),
	};
}

export default {
	async fetch(request, env, ctx) {
		if (request.method === "POST") {
			const contentType = request.headers.get("content-type");
			if (contentType?.includes("application/json")) {
				const data = await request.json();
				let cameraId = null;
				let imageBase64 = null;
				let createdDate = null;
				const snapshot = new SnapshotApi(env.SNAPSHOT_TOKEN, env.SNAPSHOT_URL);
				const survisionSerialNumber = request.headers.get(
					"survision-serial-number",
				);
				if (survisionSerialNumber) {
					cameraId = survisionSerialNumber;
					// sample 1729206290098
					createdDate = new Date(
						validInt(data["anpr"]["@date"], 10),
					).toISOString();
					imageBase64 = data["anpr"]["decision"]["jpeg"];
					ctx.waitUntil(
						snapshot.uploadBase64(
							imageBase64,
							cameraId,
							createdDate,
							requestParams(request),
						),
					);
				} else if (validGenetecEvent(data)) {
					cameraId = data["CameraName"];
					imageBase64 = data["ContextImage"];
					// "10/01/2022", Format DD/MM/YYYY
					let [month, day, year] = data["DateUtc"].split("/");
					//  "11:49:22", Format HH/MM/SS
					let [hours, minutes, seconds] = data["TimeUtc"].split(":");
					createdDate = new Date(
						validInt(year, 10),
						validInt(month, 10),
						validInt(day, 10),
						validInt(hours, 10),
						validInt(minutes, 10),
						validInt(seconds, 10),
					).toISOString();
					// Gentec camera data is larger than the queue limit (128 KB), we send directly
					ctx.waitUntil(
						snapshot.uploadBase64(
							imageBase64,
							cameraId,
							createdDate,
							requestParams(request),
						),
					);
				} else {
					return new Response("Error - Invalid Request Content", {
						status: 400,
					});
				}
				return new Response("OK!");
			} else {
				return new Response(
					"Error - Invalid Content Type, Expected application/json ",
					{ status: 400 },
				);
			}
		} else {
			return new Response("Error - Required POST", { status: 400 });
		}
	},

	// The queue handler is invoked when a batch of messages is ready to be delivered
	// https://developers.cloudflare.com/queues/platform/javascript-apis/#messagebatch
	async queue(batch, env) {
		const snapshot = new SnapshotApi(env.SNAPSHOT_TOKEN, env.SNAPSHOT_URL);
		for (const message of batch.messages) {
			console.info("Processing Queue Message:");
			console.info(message.body["cameraId"]);
			const result = await snapshot.uploadBase64(
				message.body["image"],
				message.body["cameraId"],
				message.body["timestamp"],
				message.body["params"],
			);
			console.info(`Logged Vehicle: ${JSON.stringify(result)}`);
			// Explicitly acknowledge the message as delivered
			message.ack();
		}
	},
};
