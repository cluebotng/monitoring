import os
import subprocess
from pathlib import PosixPath
from typing import Dict, Any

import yaml


class NetworkPolicies:
    binary_path = PosixPath("/workspace/bin/kubectl")

    def _restrict_prometheus_access(self) -> Dict[str, Any]:
        config = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": "restrict-prometheus-access",
                "namespace": "tool-cluebotng-monitoring",
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "app.kubernetes.io/name": "prometheus",
                    },
                },
                "ingress": [],
            },
        }

        # Grafana
        config["spec"]["ingress"].append(
            {
                "from": [
                    {
                        "podSelector": {
                            "matchLabels": {
                                "app.kubernetes.io/name": "grafana",
                            },
                        }
                    }
                ]
            }
        )

        # Grant tool related namespaces access, a 'local' pod running `alloy` will `remote_write`
        for trusted_tools in [
            "cluebot3",
            "cluebotng",
            "cluebotng-review",
            "cluebotng-staging",
            "cluebotng-trainer",
        ]:
            config["spec"]["ingress"].append(
                {
                    "from": [
                        {
                            "namespaceSelector": {
                                "matchLabels": {
                                    "name": f"tool-{trusted_tools}",
                                },
                            }
                        }
                    ]
                }
            )

        return config

    def _restrict_alertmanager_access(self) -> Dict[str, Any]:
        config = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": "restrict-alertmanager-access",
                "namespace": "tool-cluebotng-monitoring",
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "app.kubernetes.io/name": "alertmanager",
                    },
                },
                "ingress": [],
            },
        }

        # Prometheus
        config["spec"]["ingress"].append(
            {
                "from": [
                    {
                        "podSelector": {
                            "matchLabels": {
                                "app.kubernetes.io/name": "prometheus",
                            },
                        }
                    }
                ]
            }
        )

        # Grafana
        config["spec"]["ingress"].append(
            {
                "from": [
                    {
                        "podSelector": {
                            "matchLabels": {
                                "app.kubernetes.io/name": "grafana",
                            },
                        }
                    }
                ]
            }
        )

        return config

    def _apply_policy(self, policy: Dict[str, Any]) -> None:
        tool_data_dir = os.environ.get("TOOL_DATA_DIR")
        if not tool_data_dir:
            raise RuntimeError(f"No TOOL_DATA_DIR")

        kube_config = PosixPath(tool_data_dir) / ".kube" / "config"
        if not kube_config.exists():
            raise RuntimeError(f"Could not find kube config: {kube_config.as_posix()}")

        payload = yaml.dump(policy)
        p = subprocess.Popen(
            [
                self.binary_path.as_posix(),
                f"--kubeconfig={kube_config.as_posix()}",
                "apply",
                "-f",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate(payload.encode())
        if p.returncode != 0:
            raise RuntimeError(f"Failed to apply network policy: {stdout} / {stderr}")

    def apply(self):
        self._apply_policy(self._restrict_prometheus_access())
        self._apply_policy(self._restrict_alertmanager_access())
