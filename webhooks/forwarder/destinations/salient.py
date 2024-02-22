import logging

import requests
from requests.auth import HTTPBasicAuth

from .base import Destination

lgr = logging.getLogger(__name__)


class SalientCompleteView(Destination):
    name = "Salient CompleteView"

    def __init__(self, cli_args):
        self.username = cli_args.username
        self.password = cli_args.password
        self.vms = cli_args.vms
        self.camera = cli_args.camera

        super().__init__(cli_args)

    def process(self, source, description, timestamp):
        lgr.debug(
            f"Notify CompleteView Source: {source}, Description: {description}, timestamp: {timestamp}"
        )
        endpoint = "/v2.0/events"

        try:
            res = requests.post(
                f"{self.vms}{endpoint}",
                json={
                    "events": [
                        {
                            "entityType": 1,
                            "eventType": 58,
                            "eventDescription": f"Plate Detection [{description}]",
                            "user": f"Platerecognizer({source})",
                            "deviceGuid": self.camera,
                            # "streamId": 0
                        }
                    ]
                },
                auth=HTTPBasicAuth(self.username, self.password),
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
        parser = sub_parsers.add_parser(
            "salient", help=f"{SalientCompleteView.name} VMS as Events"
        )
        parser.add_argument(
            "--vms", help="Recording Server API Endpoint.", required=True
        )
        parser.add_argument(
            "--username", help="Recording Server Username.", required=True
        )
        parser.add_argument(
            "--password", help="Recording Server Password.", required=True
        )
        parser.add_argument(
            "--camera", help="UID of Camera used as Source of Events.", required=True
        )
        parser.set_defaults(func=SalientCompleteView.create)
