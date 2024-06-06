import base64
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


xml = Path(__file__).parent / "assets" / "anpr.xml"
image = Path(__file__).parent.parent.parent / "assets" / "demo.jpg"


@patch("app.parkpow.session.post")
def test_process_files(mock_post, client):
    """
    Sample Events:
    https://stackoverflow.com/a/77843753/3320006
    https://stackoverflow.com/q/75887663/3320006
    :param client:
    :return:
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {}

    response = client.post(
        "/",
        data={
            "anpr.xml": xml.open("rb"),
            "licensePlatePicture.jpg": image.open("rb"),
        },
    )

    pp_url = os.getenv("PP_URL")
    url = f"{pp_url}/api/v1/log-vehicle/"
    with open(image, "rb") as fp:
        file_content = fp.read()

    data = {
        "camera": "10.199.27.128",
        "image": base64.b64encode(file_content).decode("utf-8"),
        "results": [
            {
                "plate": "PECT600",
                "score": 0.97,
                "box": {"xmin": 691, "ymin": 397, "xmax": 750, "ymax": 431},
            }
        ],
        "time": "2024-01-19 11:17:19.000000+0800",
    }

    mock_post.assert_called_once_with(url, json=data)
    assert response.status_code == 200
    assert b"Files uploaded successfully" in response.data
