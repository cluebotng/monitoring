import configparser
import io
import os
from pathlib import PosixPath

import yaml

from monitoring.helpers import get_persistent_data_directory


class Grafana:
    home_path = PosixPath("/workspace/grafana")
    binary_path = PosixPath("/workspace/grafana/bin/grafana")
    configuration_path = PosixPath("/tmp/grafana.ini")

    def generate_grafana_configuration(self) -> str:
        tools_db_user = os.environ.get("TOOL_TOOLSDB_USER")
        if not tools_db_user:
            raise RuntimeError("Missing TOOL_TOOLSDB_USER")

        tools_db_password = os.environ.get("TOOL_TOOLSDB_PASSWORD")
        if not tools_db_password:
            raise RuntimeError("Missing TOOL_TOOLSDB_PASSWORD")

        config = configparser.ConfigParser()
        config["database"] = {
            "type": "mysql",
            "host": "tools-db",
            "name": f"{tools_db_user}__grafana",
            "user": tools_db_user,
            "password": tools_db_password,
            "max_idle_conn": 0,
            "conn_max_lifetime": 0,
        }
        config["users"] = {
            "allow_sign_up": False,
        }
        config["auth.anonymous"] = {
            "enabled": True,
            "hide_version": True,
            "org_name": "Main Org.",
            "org_role": "Viewer",
        }

        persistent_path = get_persistent_data_directory("grafana")
        config["paths"] = {
            "data": (persistent_path / "data").as_posix(),
            "plugins": (persistent_path / "plugins").as_posix(),
            "provisioning": (persistent_path / "provisioning").as_posix(),
        }

        with io.StringIO() as fh:
            config.write(fh)
            fh.seek(0)
            return fh.read()

    def generate_provisioning_configuration(self) -> str:
        return yaml.dump(
            {
                "apiVersion": 1,
                "prune": True,
                "datasources": [
                    {
                        "name": "Prometheus",
                        "type": "prometheus",
                        "access": "proxy",
                        "url": "http://prometheus:9090",
                        "isDefault": True,
                    },
                    {
                        "name": "Alertmanager",
                        "type": "alertmanager",
                        "access": "proxy",
                        "url": "http://alertmanager:9093",
                        "isDefault": True,
                    },
                ],
            }
        )

    def write_configuration(self) -> None:
        with self.configuration_path.open("w") as fh:
            fh.write(self.generate_grafana_configuration())

        persistent_path = get_persistent_data_directory("grafana")
        provisioning_dir = persistent_path / "provisioning"
        provisioning_dir.mkdir(exist_ok=True)
        with (provisioning_dir / "datasources.yaml").open("w") as fh:
            fh.write(self.generate_provisioning_configuration())

    def execute(self) -> None:
        return os.execv(
            self.binary_path.as_posix(),
            [
                self.binary_path.as_posix(),
                "server",
                "--config",
                self.configuration_path.as_posix(),
                "--homepath",
                self.home_path.as_posix(),
            ],
        )
