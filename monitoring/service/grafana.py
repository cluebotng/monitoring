import configparser
import io
import os
from pathlib import PosixPath


class Grafana:
    home_path = PosixPath("/workspace/grafana")
    binary_path = PosixPath("/workspace/grafana/bin/grafana")
    configuration_path = PosixPath("/tmp/grafana.ini")
    provisioning_path = PosixPath("/tmp/grafana-provisioning.ini")

    def generate_configuration(self) -> str:
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
        config["[paths]"] = {
            "provisioning": self.provisioning_path.as_posix(),
        }
        config["[users]"] = {
            "allow_sign_up": False,
        }
        config["[auth.anonymous]"] = {
            "enabled": True,
            "hide_version": True,
            "org_name": "Main Org.",
            "org_role": "Viewer",
        }

        with io.StringIO() as fh:
            config.write(fh)
            return fh.read()

    def write_configuration(self) -> None:
        with self.configuration_path.open("w") as fh:
            fh.write(self.generate_configuration())

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
