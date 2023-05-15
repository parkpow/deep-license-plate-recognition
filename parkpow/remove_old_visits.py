#!/usr/bin/env python
import argparse
import requests
import datetime
from urllib.parse import urlparse, parse_qs

def get_headers(authentication_token):
    return { "Authorization": f"Token {authentication_token}" }

def list_visits(api_key, max_age, hostname, page=None):
    hostname = hostname
    path = "visit-list"
    api_key = api_key
    max_age = max_age

    start_period = datetime.date.today() #today
    end_period = start_period - datetime.timedelta(days=int(max_age)) #today - max_age
    print(start_period, end_period)
    params = {
        "start": start_period,
        # "end": end_period
    }

    if page:
        params['page'] = page

    headers = get_headers(api_key)

    try:
        response = requests.get(hostname + path, params=params, headers=headers)
        print(f"Fetching visit...:")
        response.raise_for_status() 
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print("Error occurred while retrieving visit list:", str(e))
        return None

def delete_visit(hostname, api_key, visit_id):
    headers = get_headers(api_key)
    path = "delete-visit/"
    payload = {
        "id": visit_id,
    }
    try:
        print(f"Deleting visit {visit_id}...:")
        response = requests.post(hostname + path, json=payload, headers=headers)
        response.raise_for_status()

        expected_status_code = 200
        if response.status_code == expected_status_code:
            print(f"Visit {visit_id} successfully deleted!")
        else:
            print(f"Request failed. Expected status code: {expected_status_code}. Actual status code: {response.status_code}")

        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while deleting visit {visit_id} :", str(e))
        return None

if __name__ == '__main__':
    #python remove_old_visits.py --token KEY --max-age 30 --api-url https://app.parkpow.com/api/v1/
    parser = argparse.ArgumentParser(
        description='Read license plates from the images on an SFTP server and output the result as JSON or CSV.',
        epilog="",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.epilog += "Examples:\n" \
                     "Remove old visits, up to 30 days parkpow API: " \
                     "./remove_old_visits.py --token <YOUR_API_TOKEN> --max-age 30 --api-url https://app.parkpow.com/api/v1/" \
                     "Remove old visits, up to 15 days on premise environment: " \
                     "./remove_old_visits.py --token <YOUR_API_TOKEN> --max-age 30 --api-url http://local-or-public-IP:8000/"

    parser.add_argument(
        '-t',
        '--token',
        help='Cloud API Token, refer to https://app.parkpow.com/account/token/',
        required=False)

    parser.add_argument(
        '-m',
        '--max-age',
        help='number of previous days you want to delete.',
        required=False)
    
    parser.add_argument(
        '-a',
        '--api-url',
        help='Url where your visits are stored, For example: http://local-or-public-IP:8000/',
        required=False)

    cli_args = parser.parse_args()

    if not cli_args.token:
        raise Exception('token is required')
    if not cli_args.max_age:
        raise Exception('max-age is required')
    if not cli_args.max_age.isdigit() or int(cli_args.max_age) > 30:
        raise Exception('max-age is a 1 to 30 required integer')
    if not cli_args.api_url:
        raise Exception('api-url is required')
    else:
        id_list = []
        visits = list_visits(cli_args.token, cli_args.max_age, cli_args.api_url)
        while(True):
            id_list.extend([object['id'] for object in visits['results']])
            if visits['next']:
                parsed_url = urlparse(visits['next'])
                query_params = parse_qs(parsed_url.query)
                if 'page' in query_params:
                    page_value = query_params['page'][0]
                visits = list_visits(cli_args.token, cli_args.max_age, cli_args.api_url, page_value)
            else:
                break

        print(id_list)
            
    for id in id_list:
        delete_visit(cli_args.api_url, cli_args.token, id)


        