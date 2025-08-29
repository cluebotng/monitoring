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
                "receiver": "damian",
            },
            "receivers": [
                {
                    "name": "damian",
                    "email_configs": [
                        {"to": email_address}
                        for email_address in json.loads(os.environ.get("MONITORING_SEND_ALERTS_TO", "[]"))
                    ],
                }
            ],
        }

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
            ],
        )
