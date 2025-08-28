import os
from pathlib import PosixPath

import yaml


class BlackboxExporter:
    binary_path = PosixPath("/workspace/bin/blackbox_exporter")
    configuration_path = PosixPath("/tmp/blackbox_exporter.yml")

    def generate_configuration(self) -> str:
        config = {
            "modules": {
                "http_2xx": {
                    "prober": "http",
                    "http": {
                        "method": "GET",
                    },
                }
            }
        }
        return yaml.dump(config)

    def write_configuration(self) -> None:
        with self.configuration_path.open("w") as fh:
            fh.write(self.generate_configuration())

    def execute(self) -> None:
        return os.execv(
            self.binary_path.as_posix(),
            [
                self.binary_path.as_posix(),
                f"--config.file={self.configuration_path.as_posix()}",
            ],
        )
