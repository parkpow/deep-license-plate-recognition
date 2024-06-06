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


event = Path(__file__).parent / "assets" / "event.json"
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

    # https://www.axis.com/vapix-library/subjects/T10102231/section/t10165701/display?section=t10165701-t10165793
    response = client.post(
        "/",
        data={
            "event": event.open("rb"),
            "image": image.open("rb"),
        },
    )
    assert response.status_code == 200
    assert b"Files uploaded successfully" in response.data

    pp_url = os.getenv("PP_URL")
    url = f"{pp_url}/api/v1/log-vehicle/"
    with open(image, "rb") as fp:
        file_content = fp.read()

    data = {
        "camera": "ACCC8ED3290D",
        "image": base64.b64encode(file_content).decode("utf-8"),
        "results": [
            {
                "plate": "RLE11684",
                "score": "0.719034",
                "box": {"xmin": 1185, "ymin": 532, "xmax": 1325, "ymax": 560},
            }
        ],
        "time": "2021-06-11 10:05:38.252000+0000",
    }
    mock_post.assert_called_once_with(url, json=data)
