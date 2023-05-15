#!/usr/bin/env python
import argparse
import requests
import datetime
from urllib.parse import urlparse, parse_qs


def get_headers(authentication_token):
    """headers building to include in requests functions

    Args:
        authentication_token (str): authorization token comming from termminal args

    Returns:
        dictionary: fields required as heades
    """
    return {"Authorization": f"Token {authentication_token}"}


def list_visits(api_key, max_age, hostname, page=None):
    """fetchs the visits from the past <max_age> days.

    Args:
        api_key (str): Park-Pow API key
        max_age (str): Quantity of days back from today to be deleted
        hostname (str): https://<host_name>/api/v1/, For example:https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1/
        page (str, optional): API pagination number comming in data['next']. Defaults to None in first request.

    Returns:
        JSON: response from API
    """
    hostname = hostname
    path = "visit-list"
    api_key = api_key
    max_age = max_age
    end_period = datetime.date.today()
    start_period = end_period - \
        datetime.timedelta(days=int(max_age))  # today - max_age

    params = {
        "start": start_period,
    }

    if page:
        params["page"] = page

    headers = get_headers(api_key)

    try:
        response = requests.get(
            hostname + path, params=params, headers=headers)
        print(f"Fetching visit, page {'1' if not page else page}:")
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print("Error occurred while retrieving visit list:", str(e))
        return None


def delete_visit(hostname, api_key, visit_id):
    """delete individual visits by <visit_id>

    Args:
        hostname (str): https://<host_name>/api/v1/, For example:https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1/
        api_key (str): Park-Pow API key
        visit_id (str): visit identification

    Returns:
        JSON: response from API
    """
    headers = get_headers(api_key)
    path = "delete-visit/"
    payload = {
        "id": visit_id,
    }
    try:
        response = requests.post(
            hostname + path, json=payload, headers=headers)
        response.raise_for_status()

        expected_status_code = 200
        if response.status_code == expected_status_code:
            print(f"Visit {visit_id} successfully deleted!")
        else:
            print(
                f"Request failed. Expected status code: {expected_status_code}. Actual status code: {response.status_code}"
            )

        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while deleting visit {visit_id} :", str(e))
        return None


if __name__ == "__main__":
    # python remove_old_visits.py --token KEY --max-age 30 --api-url https://app.parkpow.com/api/v1/
    parser = argparse.ArgumentParser(
        description="Remove old visits up to 30 days back in Park Pow historical register",
        epilog="",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.epilog += (
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
        help="Number of previous days you want to delete.",
        required=False,
    )

    parser.add_argument(
        "-a",
        "--api-url",
        help="Url of your server API, For example: https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1",
        required=False,
    )

    cli_args = parser.parse_args()

    if not cli_args.token:
        raise Exception("token is required")
    if not cli_args.max_age:
        raise Exception("max-age is required")
    if not cli_args.max_age.isdigit() or int(cli_args.max_age) > 30:
        raise Exception("max-age is a 1 to 30 required integer")
    if not cli_args.api_url:
        raise Exception("api-url is required")
    else:
        visits_list = []
        visits = list_visits(
            cli_args.token, cli_args.max_age, cli_args.api_url)
        if any(visits["results"]):
            while True:
                visits_list.extend(
                    [
                        {"id": object["id"],
                            "start_date": object["start_date"]}
                        for object in visits["results"]
                    ]
                )
                if visits["next"]:
                    parsed_url = urlparse(visits["next"])
                    query_params = parse_qs(parsed_url.query)
                    if "page" in query_params:
                        page_value = query_params["page"][0]
                    visits = list_visits(
                        cli_args.token, cli_args.max_age, cli_args.api_url, page_value
                    )
                else:
                    break

            estimated_count = visits["estimated_count"]
            print(f"{estimated_count} visits to be deleted...")
            for visit in visits_list:
                id = visit["id"]
                start_date = visit["start_date"]
                print(f"Deleting visit {id}, date-time: {start_date}...")
                delete_visit(cli_args.api_url, cli_args.token, visit["id"])
            print('Completed!')
        else:
            print("Empty list: No visits to delete")
