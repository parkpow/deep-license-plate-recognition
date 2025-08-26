#!/usr/bin/env python
import argparse
import asyncio
import datetime
import http.client
import json
from urllib.parse import parse_qs, urlparse


async def api_request(http_function, end_point, api_key, params=None, payload=dict):
    """_summary_

    Args:
        http_function (str): options "GET" or "POST"
        end_point (str): composed by hostname + api_path
        api_key (_type_): Park-Pow API key
        params (dict, optional): key, value. End point query parameters. Defaults to None.
        payload (dict, optional): Data to be sent if required. Defaults to None.

    Returns:
        dict: response <HTTPResponse class>, connection <HTTPSConnection or HTTPConnection class>
    """

    parsed_url = urlparse(end_point)

    if parsed_url.scheme == "http":
        connection = http.client.HTTPConnection(parsed_url.hostname)
    elif parsed_url.scheme == "https":
        connection = http.client.HTTPSConnection(parsed_url.hostname)
    else:
        print("URL is not using HTTP or HTTPS")

    api_path = f"{parsed_url.path}"
    if params:
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        api_path += f"?{query_string}"

    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    try:
        connection.request(http_function, api_path, json.dumps(payload), headers)
        response = await asyncio.get_event_loop().run_in_executor(
            None, connection.getresponse
        )
        return {"response": response, "connection": connection}

    except Exception as e:
        print("Error:", e)


async def list_visits(
    api_key: str, max_age: str, hostname: str | None, page: str | None = None
):
    """lists the visits from the past <max_age> days.

    Args:
        api_key (str): Park-Pow API key
        max_age (str): Quantity of days back from today to be removed
        hostname (str): https://<host_name>/api/v1/, For example:https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1/
        page (str, optional): API pagination number comming in data['next']. Defaults to None in first request.

    Returns:
        dict: response <HTTPResponse class>, connection <HTTPSConnection or HTTPConnection class>
    """
    visit_list_path = "visit-list/"
    if hostname is None:
        raise Exception("hostname is required")
    end_point = hostname + visit_list_path
    end_period = datetime.date.today()
    start_period = end_period - datetime.timedelta(days=int(max_age))  # today - max_age

    params = {"start": start_period, "ordering": "start_date"}

    if page:
        params["page"] = page

    print(f"Fetching visit, page {'1' if not page else page}:")

    response_and_connection = await api_request(
        http_function="GET", end_point=end_point, api_key=api_key, params=params
    )
    try:
        if 200 <= response_and_connection["response"].status < 300:
            response_data = await asyncio.get_event_loop().run_in_executor(
                None, response_and_connection["response"].read
            )
            data = json.loads(response_data.decode())
            response_and_connection["connection"].close()
            return data
        else:
            raise Exception(
                f"Check parameters and try again.\x0aReason: {response_and_connection['response'].reason}"
            )
    except Exception as e:
        print("Error:", e)
        raise
    finally:
        response_and_connection["connection"].close()


async def remove_visit(hostname: str | None, api_key, visit_id):
    """remove individual visits by <visit_id>

    Args:
        hostname (str): https://<host_name>/api/v1/, For example:https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1/
        api_key (str): Park-Pow API key
        visit_id (str): visit identification str(<int>)

    Returns:
        JSON: response from API
    """
    remove_visit_path = "delete-visit/"
    if hostname is None:
        raise Exception("hostname is required")
    end_point = hostname + remove_visit_path

    payload = {"id": visit_id}

    response_and_connection = await api_request(
        http_function="POST", end_point=end_point, api_key=api_key, payload=payload
    )
    try:
        if 200 <= response_and_connection["response"].status < 300:
            print(f"Visit {visit_id} successfully removed!")
        else:
            raise Exception(
                f"Error on deleting visit.\x0aReason: {response_and_connection['response'].reason}"
            )
    except Exception as e:
        print("Error:", e)
        raise
    finally:
        response_and_connection["connection"].close()

    response_data = await asyncio.get_event_loop().run_in_executor(
        None, response_and_connection["response"].read
    )
    data = json.loads(response_data.decode())
    response_and_connection["connection"].close()
    return data


async def main():
    visits_list = []
    removed_count = 0
    visits = await list_visits(cli_args.token, cli_args.max_age, cli_args.api_url)
    if any(visits["results"]):
        while True:
            visits_list.extend(visits["results"])
            if visits["next"]:
                parsed_url = urlparse(visits["next"])
                query_params = parse_qs(parsed_url.query)
                if "page" in query_params:
                    page_value = query_params["page"][0]

                visits = await list_visits(
                    cli_args.token, cli_args.max_age, cli_args.api_url, page_value
                )
            else:
                break

        estimated_count = visits["estimated_count"]
        print(f"{estimated_count} visits to be removed...")
        for visit in visits_list:
            id = visit["id"]
            start_date = visit["start_date"]
            print(f"Deleting visit {id}, date-time: {start_date}")
            await remove_visit(cli_args.api_url, cli_args.token, visit["id"])
            removed_count += 1
        print(f"Completed, {str(removed_count)} of {estimated_count} visits removed")
    else:
        print("Empty list: No visits to remove")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove old visits up to 30 days back in Park Pow historical register",
        epilog="",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.epilog += (  # type: ignore
        "Examples:\n"
        "Remove old visits, up to 30 days parkpow API: "
        "./remove_old_visits.py --token <YOUR_API_TOKEN> --max-age 30 --api-url https://app.parkpow.com/api/v1/"
        "Remove old visits, up to 15 days on premise environment: "
        "./remove_old_visits.py --token <YOUR_API_TOKEN> --max-age 30 --api-url http://local-or-public-IP:8000/api/v1/"
    )

    parser.add_argument(
        "-t",
        "--token",
        help="ParkPow API Token, refer to https://app.parkpow.com/account/token/",
        required=False,
    )

    parser.add_argument(
        "-m",
        "--max-age",
        help="Number of previous days you want to remove.",
        type=int,
        required=True,
    )

    parser.add_argument(
        "-a",
        "--api-url",
        help="Url of your server API, For example: https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1",
        required=False,
    )

    cli_args = parser.parse_args()

    print(cli_args.max_age)
    if not cli_args.token:
        raise Exception("token is required")
    if not cli_args.max_age:
        raise Exception("max-age is required")
    if cli_args.max_age < 1 or cli_args.max_age > 30:
        raise Exception("max-age must be in range  1 to 30")
    if not cli_args.api_url:
        raise Exception("api-url is required")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
