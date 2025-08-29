export class UnexpectedApiResponse extends Error {
  constructor(message, status) {
    super(message);
    this.name = "UnexpectedApiResponse";
    this.status = status;
  }
}

export class Error429 extends UnexpectedApiResponse {
  constructor(message) {
    super(message, 429);
    this.name = "429Error";
  }
}

export class Error5xx extends UnexpectedApiResponse {
  constructor(message, status) {
    super(message, status);
    this.name = "5xxError";
  }
}

export class RetryLimit extends UnexpectedApiResponse {
  constructor(message, status) {
    super(message, status);
    this.name = "RetryLimit";
  }
}

export class InvalidIntValue extends Error {
  constructor(message) {
    super(message);
    this.name = "InvalidIntValue";
  }
}

export class InvalidResults extends UnexpectedApiResponse {
  constructor(message) {
    super(message);
    this.name = "InvalidIntValue";
  }
}
