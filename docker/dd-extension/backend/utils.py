try:
    from urllib.error import URLError
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, URLError, urlopen  # type: ignore
from ssl import SSLError


def verify_token(token, license_key, is_stream=True):
    if not token or not license_key:
        raise ValueError("API token and license key is required.")

    path = "stream/license" if is_stream else "sdk-webhooks"
    try:
        req = Request(
            f"https://api.platerecognizer.com/v1/{path}/{license_key.strip()}/"
        )
        req.add_header("Authorization", f"Token {token.strip()}")
        urlopen(req).read()
        return True, None

    except SSLError:
        req = Request(
            f"http://api.platerecognizer.com/v1/{path}/{license_key.strip()}/"
        )
        req.add_header("Authorization", f"Token {token.strip()}")
        urlopen(req).read()
        return True, None

    except URLError as e:
        if "404" in str(e):
            return (
                False,
                "The License Key cannot be found. Please use the correct License Key.",
            )
        elif str(403) in str(e):
            return False, "The API Token cannot be found. Please use the correct Token."

        else:
            return True, None
