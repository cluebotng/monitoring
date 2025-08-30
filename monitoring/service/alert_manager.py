import json
import os
from pathlib import PosixPath

import yaml

from monitoring.helpers import get_persistent_data_directory


class AlertManager:
    files_path = PosixPath(__file__).parent.parent / "alertmanager"
    binary_path = PosixPath("/workspace/bin/alertmanager")
    configuration_path = PosixPath("/tmp/alertmanager.yml")

    def generate_configuration(self) -> str:
        send_alerts_to = json.loads(os.environ.get("MONITORING_SEND_ALERTS_TO", "[]"))

        config = {
            "templates": [],
            "global": {
                "smtp_from": "ClueBot Monitoring <tools.cluebotng-monitoring@toolforge.org>",
                "smtp_smarthost": "mail.tools.wmcloud.org:25",
            },
            "route": {
                "group_by": ["alertname", "cluster", "service"],
                "group_wait": "30s",
                "group_interval": "5m",
                "repeat_interval": "12h",
                "receiver": "email_contacts",
                "routes": [
                    {
                        "receiver": "wiki-updater",
                        "group_wait": "1m",
                        "matchers": [
                            "update_wiki_host=~.+",
                            "update_wiki_page=~.+",
                        ],
                    }
                ],
            },
            "receivers": [
                {
                    "name": "wiki-updater",
                    "webhook_configs": [
                        {
                            "send_resolved": True,
                            "url": "http://wiki-update-receiver/alertmanager",
                        }
                    ],
                },
            ],
        }

        # Calculate receivers
        email_contacts = {
            "name": "email_contacts",
        }
        wiki_updater = {
            "name": "wiki-updater",
            "webhook_configs": [
                {
                    "send_resolved": True,
                    "url": "http://wiki-update-receiver:8900/alertmanager",
                }
            ],
        }

        if send_alerts_to:
            # Email
            email_configs = [
                {"to": email_address} for email_address in send_alerts_to
            ]
            email_contacts["email_configs"] = email_configs
            wiki_updater["email_configs"] = email_configs
        else:
            # Placeholder
            email_contacts["webhook_configs"] = [
                {"send_resolved": False, "url": "http://invalid.host"}
            ]

        config["receivers"] = [email_contacts, wiki_updater]

        # Include any template files
        if template_files := [
            path.absolute().as_posix()
            for path in (self.files_path / "template").glob("*.tmpl")
        ]:
            config["templates"] = template_files

        return yaml.dump(config)

    def write_configuration(self) -> None:
        with self.configuration_path.open("w") as fh:
            fh.write(self.generate_configuration())

    def execute(self) -> None:
        return os.execv(
            self.binary_path.as_posix(),
            [
                self.binary_path.as_posix(),
                "--config.file",
                self.configuration_path.as_posix(),
                "--storage.path",
                get_persistent_data_directory("alert-manager").as_posix(),
                "--log.level=debug",
            ],
        )
