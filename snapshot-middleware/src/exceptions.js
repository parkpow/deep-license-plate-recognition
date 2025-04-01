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

export class RetryLimit extends Error {
  constructor(message) {
    super(message);
    this.name = "RetryLimit";
  }
}

export class UnexpectedApiResponse extends Error {
  constructor(message, status) {
    super(message);
    this.name = "UnexpectedApiResponse";
    this.status = status;
  }
}

export class InvalidIntValue extends Error {
  constructor(message) {
    super(message);
    this.name = "InvalidIntValue";
  }
}
