import logging
import os
import sys

from flask import Flask, request
from utils import verify_token

LOG_LEVEL = os.environ.get("LOGGING", "DEBUG").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)


app = Flask(__name__)


@app.route("/verify-token", methods=["POST"])
def verify_token_license():
    lgr.debug(f"verify token data: {request.data}")
    token = request.json.get("token")
    license = request.json.get("license")
    try:
        valid, message = verify_token(token, license, "port" not in request.json)
    except ValueError as e:
        valid = False
        message = str(e)

    lgr.info(f"verify result: {valid} - {message}")

    return {"valid": valid, "message": message}


if __name__ == "__main__":
    app.run()
