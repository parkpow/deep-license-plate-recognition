import logging

import requests
from requests.auth import HTTPDigestAuth

from .base import Destination

lgr = logging.getLogger(__name__)


class Nx(Destination):
    name = "NX VMS"

    def __init__(self, cli_args):
        self.username = cli_args.username
        self.password = cli_args.password
        self.vms = cli_args.vms
        self.camera = cli_args.camera

        super().__init__(cli_args)

    def process(self, source, description, timestamp):
        lgr.debug(
            f"Notify NX Source: {source}, Description: {description}, timestamp: {timestamp}"
        )
        endpoint = "/api/createEvent"

        try:
            res = requests.get(
                f"{self.vms}{endpoint}",
                params={
                    "timestamp": timestamp,
                    "source": source,
                    "caption": "New Plate Detection",
                    "metadata": '{"cameraRefs":["' + self.camera + '"]}',
                    "description": description,
                },
                auth=HTTPDigestAuth(self.username, self.password),
                verify=False,
            )
            res.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            lgr.error("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            lgr.error("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            lgr.error("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            lgr.error("OOps: Something Else", err)

    @staticmethod
    def add_cli_arguments(sub_parsers):
        parser = sub_parsers.add_parser("nx", help=f"{Nx.name} as Alerts")
        parser.add_argument("--username", help="NX VMS Username.", required=True)
        parser.add_argument("--password", help="NX VMS Password.", required=True)
        parser.add_argument("--vms", help="VMS API Endpoint.", required=True)
        parser.add_argument(
            "--camera", help="UID of Camera used as Source of Alerts.", required=True
        )
        parser.set_defaults(func=Nx.create)
