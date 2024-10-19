import { SnapshotApi } from "./snapshot";

export default {
	async fetch(request, env, ctx) {
		if (request.method === "POST") {
			const contentType = request.headers.get("content-type");
			if (contentType.includes("application/json")) {
				const data = await request.json();
				console.debug(data);
				let cameraId = null;
				let imageBase64 = null;
				let createdDate = null;
				const survisionSerialNumber = request.headers.get(
					"survision-serial-number",
				);
				if (survisionSerialNumber) {
					cameraId = survisionSerialNumber;
					createdDate = new Date(parseInt(data["anpr"]["@date"])).toISOString(); // sample 1729206290098
					imageBase64 = data["anpr"]["decision"]["jpeg"];
				} else {
					cameraId = data["CameraName"];
					imageBase64 = data["ContextImage"];
					// "10/01/2022", Format DD/MM/YYYY
					let [day, month, year] = data["DateUtc"].split("/");
					//  "11:49:22", Format HH/MM/SS
					let [hours, minutes, seconds] = data["TimeUtc"].split(":");
					createdDate = new Date(
						parseInt(year),
						parseInt(month),
						parseInt(day),
						parseInt(hours),
						parseInt(minutes),
						parseInt(seconds),
					).toISOString();
				}
				ctx.waitUntil(
					env.INCOMING_WEBHOOKS.send({
						image: imageBase64,
						cameraId: cameraId,
						timestamp: createdDate,
					}),
				);
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
			const result = await snapshot.uploadBase64(
				message.body["image"],
				message.body["cameraId"],
				message.body["timestamp"],
			);
			console.info(`Logged Vehicle: ${JSON.stringify(result)}`);
			// Explicitly acknowledge the message as delivered
			message.ack();
		}
	},
};
