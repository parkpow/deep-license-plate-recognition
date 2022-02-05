from unittest import mock

import pytest
import requests

from .functions import WebhookError, WebhookTester


class TestWebhookTester:
    """A collection of test cases for webhook tester."""

    @mock.patch.object(requests, "get")
    @mock.patch.object(requests, "post")
    def test_send_request(self, mock_post, mock_get):
        """Test successful response when executing send_request."""
        mock_get.return_value.status_code = 200
        mock_post.return_value.status_code = 201

        image_url = ("https://platerecognizer.com/wp-content/uploads/2020/07/"
                     "ALPR-license-plate-reader-images-API.jpg")
        url = "https://example.com"
        tester = WebhookTester(url)
        data = tester.get_webhook_payload()
        files = {"upload": {"name": b"sample file content"}}
        options = [{
            "method": "get",
            "kwargs": {
                "url": image_url
            },
        }, {
            "method": "post",
            "kwargs": {
                "url": "https://example.com",
                "data": data,
                "files": files
            },
        }]

        for option in options:
            response = tester.send_request(
                option["method"],
                **option["kwargs"],
            )

            if option["method"] == "get":
                assert response.status_code == 200
            else:
                assert response.status_code == 201

    def test_send_request_exceptions(self):
        """Test successful exception handling in send_request method."""
        exceptions = [
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.RequestException,
        ]
        tester = WebhookTester("https://example.com")
        for exception in exceptions:
            with mock.patch.object(requests, "post") as mock_post:
                mock_post.side_effect = exception

                with pytest.raises(WebhookError) as _:
                    tester.send_request("post", tester.url)

    def test_send_request_method_not_supported(self):
        """
        Test method validation in send_request method.

        Only accepts get and post methods.
        """
        tester = WebhookTester("https://example.com")
        with pytest.raises(ValueError) as _:
            tester.send_request("put", tester.url)
