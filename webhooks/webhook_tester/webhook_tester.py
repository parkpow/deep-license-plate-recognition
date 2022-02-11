import os

from functions import WebhookTester

if __name__ == "__main__":
    url = os.environ.get("URL")
    if not url:
        raise ValueError("Set URL environment variable when running docker.")
    try:
        tester = WebhookTester(url)
        tester.execute()
    except KeyboardInterrupt:
        print('Stopping...')
    except Exception as e:
        print('--> An error occured:')
        print(e)
        print('--> The webhook failed.')
