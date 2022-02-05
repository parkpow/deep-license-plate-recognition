import os

from .functions import WebhookTester

if __name__ == "__main__":
    url = os.environ.get("URL")
    if not url:
        raise ValueError("Set URL environment variable when running docker.")

    tester = WebhookTester(url)
    tester.execute()
