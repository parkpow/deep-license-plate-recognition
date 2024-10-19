export class Error429 extends Error {
	constructor({ message, response }) {
		super(message);
		this.name = "429Error";
		this.data = response;
	}
}

export class Error5xx extends Error {
	constructor({ message, response }) {
		super(message);
		this.name = "5xxError";
		this.data = response;
	}
}
