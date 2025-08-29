import os
from pathlib import PosixPath

import yaml

from monitoring.helpers import get_persistent_data_directory


class Prometheus:
    files_path = PosixPath(__file__).parent.parent.parent / "prometheus"
    binary_path = PosixPath("/workspace/bin/prometheus")
    configuration_path = PosixPath("/tmp/prometheus.yml")

    def generate_configuration(self) -> str:
        config = {
            "global": {
                "scrape_interval": "60s",
                "evaluation_interval": "60s",
                "scrape_timeout": "10s",
            },
            "scrape_configs": [],
            "alerting": {
                "alertmanagers": [
                    {"static_configs": [{"targets": ["alertmanager:9093"]}]}
                ]
            },
        }

        if rule_files := [
            path.absolute().as_posix()
            for path in (self.files_path / "rules").glob("*.yml")
        ]:
            config["rule_files"] = rule_files

        # Self
        config["scrape_configs"].append(
            {
                "job_name": "prometheus",
                "static_configs": [{"targets": ["localhost:9090"]}],
            }
        )

        # Alertmanager
        config["scrape_configs"].append(
            {
                "job_name": "alertmanager",
                "static_configs": [{"targets": ["alertmanager:9093"]}],
            }
        )

        # Checker
        config["scrape_configs"].append(
            {
                "job_name": "checker",
                "static_configs": [{"targets": ["checker:8090"]}],
            }
        )

        # Blackbox probes
        config["scrape_configs"].append(
            {
                "job_name": "blackbox",
                "metrics_path": "/probe",
                "params": {
                    "module": [
                        "http_2xx",
                    ],
                },
                "static_configs": [
                    {
                        "targets": [
                            "cluebotng.toolforge.org",
                            "cluebotng-review.toolforge.org",
                            "cluebotng-editsets.toolforge.org",
                            "cluebotng-staging.toolforge.org",
                            "cluebotng-trainer.toolforge.org",
                        ]
                    }
                ],
                "relabel_configs": [
                    {
                        "source_labels": ["__address__"],
                        "target_label": "__param_target",
                    },
                    {"source_labels": ["__param_target"], "target_label": "instance"},
                    {
                        "target_label": "__address__",
                        "replacement": "blackbox-exporter:9115",
                    },
                ],
            }
        )

        # Blackbox metrics
        config["scrape_configs"].append(
            {
                "job_name": "blackbox_exporter",
                "static_configs": [{"targets": ["blackbox-exporter:9115"]}],
            }
        )

        # Note: Most metrics are pushed via grafana-alloy
        return yaml.dump(config)

    def write_configuration(self) -> None:
        with self.configuration_path.open("w") as fh:
            fh.write(self.generate_configuration())

    def execute(self) -> None:
        tool_data_dir = os.environ.get("TOOL_DATA_DIR")
        if not tool_data_dir:
            raise RuntimeError(f"No TOOL_DATA_DIR")

        home_dir = PosixPath(tool_data_dir)
        if not home_dir.exists():
            raise RuntimeError(f"Data directory does not exist: {home_dir.as_posix()}")

        return os.execv(
            self.binary_path.as_posix(),
            [
                self.binary_path.as_posix(),
                "--web.enable-remote-write-receiver",
                "--config.file",
                self.configuration_path.as_posix(),
                "--storage.tsdb.path",
                get_persistent_data_directory("prometheus").as_posix(),
                "--storage.tsdb.retention.time",
                "90d",
            ],
        )
