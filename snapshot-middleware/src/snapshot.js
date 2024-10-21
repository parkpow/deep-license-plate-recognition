import { fetchWithRetry } from "./utils";

export class SnapshotApi {
	constructor(token, sdkUrl = null) {
		if (token === null) {
			throw new Error("Snapshot API token is required for authentication.");
		} else {
			this.token = token;
		}
		if (sdkUrl) {
			this.apiBase = sdkUrl;
		} else {
			this.apiBase = "https://api.platerecognizer.com";
		}
		console.debug("Api Base: " + this.apiBase);
	}

	async uploadBase64(encodedImage, camera, timestamp) {
		const endpoint = "/v1/plate-reader/";
		const body = new FormData();
		body.set("camera_id", camera);
		body.set("upload", encodedImage);
		body.set("timestamp", timestamp);
		body.set("mmc", "true");
		let init = {
			body: body,
			method: "POST",
			headers: {
				Authorization: "Token " + this.token,
			},
		};
		const url = this.apiBase + endpoint;
		return fetchWithRetry(url, init).then((response) => response.json());
	}
}
