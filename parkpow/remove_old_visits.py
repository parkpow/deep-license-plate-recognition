#!/usr/bin/env python
import asyncio
import http.client
import argparse
import requests
import datetime
import json
from urllib.parse import urlparse, parse_qs

def get_headers(authentication_token):
    """headers building to include in requests functions

    Args:
        authentication_token (str): authorization token comming from termminal args

    Returns:
        dictionary: fields required as heades
    """
    return {"Authorization": f"Token {authentication_token}"}

async def api_fetch(url, headers=None, params=None):
    """Asynchronous API fetch function

    Args:
        url (str): hostname + API path
        headers (dict, optional): Required headers as Authorization. Defaults to None.
        params (dict, optional): Request to set url parameters. Defaults to None.

    Returns:
        dict: response <HTTPResponse class>, connection <HTTPSConnection or HTTPConnection class>
    """
    parsed_url = urlparse(url)

    if parsed_url.scheme == "http":
        connection = http.client.HTTPConnection(parsed_url.hostname)    
    elif parsed_url.scheme == "https":
        connection = http.client.HTTPSConnection(parsed_url.hostname)
    else:
        print("URL is not using HTTP or HTTPS")
    
    if params:
        api_path = f"{parsed_url.path}"
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        url_with_params = f"{api_path}?{query_string}"
        
    try: 
        connection.request("GET", url_with_params, headers=headers)
        response = await asyncio.get_event_loop().run_in_executor(None, connection.getresponse)
        return {'response':response, 'connection':connection}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

async def api_post(url, data=None, headers=None):
    """Asynchronous API post function
       
    Args:
        url (str): hostname + API path
        data (dict, optional): payload to send.
        headers (dict, optional): Required headers as Authorization. Defaults to None.

    Returns:
        dict: response <HTTPResponse class>, connection <HTTPSConnection or HTTPConnection class>
    """
    parsed_url = urlparse(url)

    if parsed_url.scheme == "http":
        connection = http.client.HTTPConnection(parsed_url.hostname)
    elif parsed_url.scheme == "https":
        connection = http.client.HTTPSConnection(parsed_url.hostname)
    else:
        print("URL is not using HTTP or HTTPS")

    api_path = parsed_url.path
    
    try:
        connection.request("POST", api_path, json.dumps(data), headers)
        response = await asyncio.get_event_loop().run_in_executor(None, connection.getresponse)
        return {'response':response, 'connection':connection}
    
    except Exception as e:
        print("Error:", e)

async def list_visits(api_key, max_age, hostname, page=None):
    """lists the visits from the past <max_age> days.

    Args:
        api_key (str): Park-Pow API key
        max_age (str): Quantity of days back from today to be removed
        hostname (str): https://<host_name>/api/v1/, For example:https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1/
        page (str, optional): API pagination number comming in data['next']. Defaults to None in first request.

    Returns:
        dict: response <HTTPResponse class>, connection <HTTPSConnection or HTTPConnection class>
    """
    api_url = hostname
    visit_list_path = "visit-list/"
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

    print(f"Fetching visit, page {'1' if not page else page}:")
    response_and_connection = await api_fetch(api_url + visit_list_path, headers, params)
    
    expected_status_code = 200
    if response_and_connection['response'].status == expected_status_code:
        response_data = await asyncio.get_event_loop().run_in_executor(None, response_and_connection['response'].read)
        data = json.loads(response_data.decode())
        response_and_connection['connection'].close()
        return data
    else:
        raise Exception(f"Request failed. Expected status code: {expected_status_code}. Actual status code: {response_and_connection['response'].status}.\x0aCheck parameters and try again...")

async def remove_visit(hostname, api_key, visit_id):
    """remove individual visits by <visit_id>

    Args:
        hostname (str): https://<host_name>/api/v1/, For example:https://app.parkpow.com/api/v1/ or http://local-or-public-IP:8000/api/v1/
        api_key (str): Park-Pow API key
        visit_id (str): visit identification str(<int>)

    Returns:
        JSON: response from API
    """
    api_url = hostname
    headers = get_headers(api_key)
    headers['Content-Type'] = "application/json"
    
    remove_visit_path = "delete-visit/"
    payload = {
        "id": visit_id,
    }
    response_and_connection = await api_post(api_url + remove_visit_path, payload, headers)

    expected_status_code = 200
    if response_and_connection['response'].status == expected_status_code:
        print(f"Visit {visit_id} successfully removed!")
    else:
        raise Exception(f"Request failed. Expected status code: {expected_status_code}. Actual status code: {response_and_connection['response'].status}.\x0aReason: {response_and_connection['response'].reason}")
    
    response_data = await asyncio.get_event_loop().run_in_executor(None, response_and_connection['response'].read)
    data = json.loads(response_data.decode())
    response_and_connection['connection'].close()
    return data

async def main():
    
    visits_list = []
    removed_count = 0
    visits = await list_visits(cli_args.token, cli_args.max_age, cli_args.api_url)
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
                visits = await list_visits(
                    cli_args.token, cli_args.max_age, cli_args.api_url, page_value
                )
            else:
                break

        estimated_count = visits["estimated_count"]
        print(f"{estimated_count} visits to be removed...")
        #reverse=False, oldest first | reverse=True newest first
        sorted_visit_list = sorted(visits_list, key=lambda x: x['start_date'], reverse=False)
        for visit in sorted_visit_list:
            id = visit["id"]
            start_date = visit["start_date"]
            print(f"Deleting visit {id}, date-time: {start_date}")
            await remove_visit(cli_args.api_url, cli_args.token, visit["id"])
            removed_count += 1
        print(f'Completed, {str(removed_count)} of {estimated_count} visits removed')
    else:
        print("Empty list: No visits to remove")
        
if __name__ == "__main__":
    
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
        help="Number of previous days you want to remove.",
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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())