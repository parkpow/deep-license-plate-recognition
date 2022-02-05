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
        files = {"upload": ("name", b"sample file content")}
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

    @mock.patch.object(requests, "get")
    def test_get_files_payload(self, mock_get):
        """Test successful retrieval of files payload."""
        mock_get.return_value.content = b"Sample content"
        tester = WebhookTester("https://example.com")
        payload = tester.get_files_payload()
        assert payload
        assert payload["upload"][0]

    @mock.patch.object(requests, "get")
    @mock.patch.object(requests, "post")
    def test_execute_tester(self, mock_post, mock_get, capsys):
        """Test successful execution of webhook tester."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"Sample content"
        mock_post.return_value.status_code = 201

        tester = WebhookTester("https://example.com")
        tester.execute()
        captured = capsys.readouterr()
        assert "Status Code: 201" in captured.out

    @mock.patch.object(requests, "get")
    @mock.patch.object(requests, "post")
    def test_execute_tester_raise_error(self, mock_post, mock_get, capsys):
        """Test raising of WebhookError if status code is more than 300."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"Sample content"
        mock_post.return_value.status_code = 400
        mock_post.return_value.content = "Something went wrong"

        tester = WebhookTester("https://example.com")
        with pytest.raises(WebhookError) as _:
            tester.execute()

            captured = capsys.readouterr()
            assert "Status 400" in captured.out
            assert "Something went wrong" in captured.out
