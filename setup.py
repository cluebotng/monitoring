#!/usr/bin/env python3
import os
import subprocess
from pathlib import PosixPath

BASE_PATH = PosixPath("/workspace")
RELEASE_PROMETHEUS = "3.5.0"
RELEASE_ALERT_MANAGER = "0.28.1"
RELEASE_BLACKBOX_EXPORTER = "0.27.0"
RELEASE_KUBECTL = "v1.34.0"
RELEASE_GRAFANA = "12.1.1"
RELEASE_GRAFANA_HASH = "16903967602"


def setup():
    (BASE_PATH / "bin").mkdir(parents=True, exist_ok=True)


def install_prometheus():
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "-L",
            "-o",
            f"/tmp/prometheus-{RELEASE_PROMETHEUS}.linux-amd64.tar.gz",
            f"https://github.com/prometheus/prometheus/releases/download/v{RELEASE_PROMETHEUS}/"
            f"prometheus-{RELEASE_PROMETHEUS}.linux-amd64.tar.gz",
        ],
        check=True,
    )
    subprocess.run(
        [
            "tar",
            "-C",
            (BASE_PATH / "bin").as_posix(),
            "-xf",
            f"/tmp/prometheus-{RELEASE_PROMETHEUS}.linux-amd64.tar.gz",
            "--strip-components=1",
            f"prometheus-{RELEASE_PROMETHEUS}.linux-amd64/prometheus",
            f"prometheus-{RELEASE_PROMETHEUS}.linux-amd64/promtool",
        ],
        check=True,
    )
    os.remove(f"/tmp/prometheus-{RELEASE_PROMETHEUS}.linux-amd64.tar.gz")


def install_alertmanager():
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "-L",
            "-o",
            f"/tmp/alertmanager-{RELEASE_ALERT_MANAGER}.linux-amd64.tar.gz",
            f"https://github.com/prometheus/alertmanager/releases/download/v{RELEASE_ALERT_MANAGER}/"
            f"alertmanager-{RELEASE_ALERT_MANAGER}.linux-amd64.tar.gz",
        ],
        check=True,
    )
    subprocess.run(
        [
            "tar",
            "-C",
            (BASE_PATH / "bin").as_posix(),
            "-xf",
            f"/tmp/alertmanager-{RELEASE_ALERT_MANAGER}.linux-amd64.tar.gz",
            "--strip-components=1",
            f"alertmanager-{RELEASE_ALERT_MANAGER}.linux-amd64/alertmanager",
        ],
        check=True,
    )
    os.remove(f"/tmp/alertmanager-{RELEASE_ALERT_MANAGER}.linux-amd64.tar.gz")


def install_blackbox_exporter():
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "-L",
            "-o",
            f"/tmp/blackbox_exporter-{RELEASE_BLACKBOX_EXPORTER}.linux-amd64.tar.gz",
            f"https://github.com/prometheus/blackbox_exporter/releases/download/v{RELEASE_BLACKBOX_EXPORTER}/"
            f"blackbox_exporter-{RELEASE_BLACKBOX_EXPORTER}.linux-amd64.tar.gz",
        ],
        check=True,
    )
    subprocess.run(
        [
            "tar",
            "-C",
            (BASE_PATH / "bin").as_posix(),
            "-xf",
            f"/tmp/blackbox_exporter-{RELEASE_BLACKBOX_EXPORTER}.linux-amd64.tar.gz",
            "--strip-components=1",
            f"blackbox_exporter-{RELEASE_BLACKBOX_EXPORTER}.linux-amd64/blackbox_exporter",
        ],
        check=True,
    )
    os.remove(f"/tmp/blackbox_exporter-{RELEASE_BLACKBOX_EXPORTER}.linux-amd64.tar.gz")


def install_grafana():
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "-L",
            "-o",
            f"/tmp/grafana_{RELEASE_GRAFANA}_{RELEASE_GRAFANA_HASH}_linux_amd64.tar.gz",
            f"https://dl.grafana.com/grafana/release/{RELEASE_GRAFANA}/"
            f"grafana_{RELEASE_GRAFANA}_{RELEASE_GRAFANA_HASH}_linux_amd64.tar.gz",
        ],
        check=True,
    )

    target_path = BASE_PATH / "grafana"
    target_path.mkdir()
    subprocess.run(
        [
            "tar",
            "-C",
            target_path.as_posix(),
            "-xf",
            f"/tmp/grafana_{RELEASE_GRAFANA}_{RELEASE_GRAFANA_HASH}_linux_amd64.tar.gz",
            "--strip-components=1",
        ],
        check=True,
    )
    os.remove(
        f"/tmp/grafana_{RELEASE_GRAFANA}_{RELEASE_GRAFANA_HASH}_linux_amd64.tar.gz"
    )


def install_kubectl():
    target_path = BASE_PATH / "bin" / "kubectl"
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "-L",
            "-o",
            target_path.as_posix(),
            f"https://dl.k8s.io/release/{RELEASE_KUBECTL}/bin/linux/amd64/kubectl",
        ],
        check=True,
    )
    target_path.chmod(0x555)


def appease_poetry():
    # Poetry expects a Python package from `setup.py install`, create a minimal one
    package_dir = PosixPath("/workspace/haproxy")
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").open("w").close()


def main():
    setup()
    install_prometheus()
    install_alertmanager()
    install_blackbox_exporter()
    install_kubectl()
    install_grafana()
    appease_poetry()


if __name__ == "__main__":
    main()
