import argparse
import datetime

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description="Measure ParkPow load time.")
    parser.add_argument(
        "--url",
        help="The base URL of the ParkPow website. Defaults to localhost.",
        default="http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--email",
        help="The email address to be used for login",
    )
    parser.add_argument(
        "--password",
        help="The corresponding password for the provided email.",
    )
    return parser.parse_args()


def login(session, url, email, password):
    login_url = f"{url}/accounts/login/"

    res1 = session.get(login_url)
    csrf_token = res1.cookies["csrftoken"]
    res2 = session.post(
        login_url,
        data={"login": email, "password": password, "csrfmiddlewaretoken": csrf_token},
    )
    return "dashboard" in res2.url


def _get_load_time_or_none(res):
    if res.status_code == 200:
        return res.elapsed.microseconds / 1000
    else:
        return None


def get_first_plate(session, url):
    _url = f"{url}/api/v1/vehicles/"
    res = session.get(_url)
    if res.status_code == 200:
        return res.json()["results"][0]["license_plate"]
    return False


def get_first_camera(session, url):
    _url = f"{url}/api/v1/visit-list/"
    res = session.get(_url)
    if res.status_code == 200:
        return res.json()["results"][0]["start_cam"]["name"]


def get_load_time(session, url, path="dashboard", days=1):
    url = f"{url}/{path}/"

    time_delta = datetime.timedelta(days=days)
    dt_from = datetime.datetime.now() - time_delta

    res = session.get(url, params={"from": dt_from})

    return _get_load_time_or_none(res)


def get_load_time_search_plate(session, url, plate, path="dashboard", days=1):
    url = f"{url}/{path}/"
    time_delta = datetime.timedelta(days=days)

    dt_from = datetime.datetime.now() - time_delta
    res = session.get(url, params={"from": dt_from, "plate": plate})

    return _get_load_time_or_none(res)


def get_load_time_filter_by_camera(session, url, camera_name, path="dashboard", days=1):
    url = f"{url}/{path}/"
    time_delta = datetime.timedelta(days=days)

    dt_from = datetime.datetime.now() - time_delta
    res = session.get(url, params={"from": dt_from, "camera_name": camera_name})

    return _get_load_time_or_none(res)


def get_result(session, url, path, plate, camera):
    for day in [1, 7, 14, 30, 60]:
        load_time = get_load_time(session, url, path, day)
        load_time_plate = get_load_time_search_plate(session, url, plate, path, day)
        load_time_camera = get_load_time_filter_by_camera(
            session, url, camera, path, day
        )

        load_time_str = f"{load_time}ms" if load_time else "failed to load"
        load_time_plate_str = (
            f"{load_time_plate}ms" if load_time_plate else "failed to load"
        )
        load_time_camera_str = (
            f"{load_time_camera}ms" if load_time_camera else "failed to load"
        )

        yield dict(
            day=day,
            no_filter=load_time_str,
            filter_plate=load_time_plate_str,
            filter_camera=load_time_camera_str,
        )


def print_table(title, results):
    if not results:
        return
    print("| -------------------------------------------------------------------- |")
    print(f"|{title.center(70)}|")
    print("| -------------------------------------------------------------------- |")
    print("|   Range   | Without filter  | License plate search | Filter 1 camera |")
    print("| --------- | --------------- | -------------------- | --------------- |")
    for result in results:
        print(
            "| {day:2n} day(s) | {no_filter:^15s} | {filter_plate:^20s} | {filter_camera:^15s} |".format(
                **result
            )
        )
    print("| -------------------------------------------------------------------- |")


def main():
    session = requests.session()
    args = parse_arguments()

    if not args.email or not args.password:
        print("Provide a valid credential with --email and --password. Exiting...")
        return

    # Login
    print("Logging in...")
    if not login(session, args.url, args.email, args.password):
        print("Login failed. Exiting...")
        return

    print()

    plate = get_first_plate(session, args.url)
    camera = get_first_camera(session, args.url)

    if not plate:
        print("Failed to get a plate to search")
        return

    if not camera:
        print("Failed to get a camera for filtering")
        return

    # Dashboard
    results = get_result(session, args.url, "dashboard", plate, camera)
    print_table("Dashboard", results)

    print()
    print()

    # Dashboard statistics
    results = get_result(session, args.url, "dashboard/?statistics=true", plate, camera)
    print_table("Dashboard Statistics", results)

    print()
    print()

    # Dashboard chart
    results = get_result(session, args.url, "dashboard/?chart-data=true", plate, camera)
    print_table("Dashboard Chart", results)

    print()
    print()

    # Alert
    results = get_result(session, args.url, "alerts", plate, camera)
    print_table("Alert", results)


if __name__ == "__main__":
    main()
