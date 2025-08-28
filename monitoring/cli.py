#!/usr/bin/env python3
import logging
import sys

import click

from monitoring.maintenance.network_policies import NetworkPolicies
from monitoring.service.alert_manager import AlertManager
from monitoring.service.blackbox_exporter import BlackboxExporter
from monitoring.service.grafana import Grafana
from monitoring.service.prometheus import Prometheus


@click.group()
def cli():
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


@cli.command()
def prometheus():
    network_policies = NetworkPolicies()
    network_policies.apply()

    service = Prometheus()
    service.write_configuration()
    service.execute()


@cli.command()
def alert_manager():
    service = AlertManager()
    service.write_configuration()
    service.execute()


@cli.command()
def blackbox_exporter():
    service = BlackboxExporter()
    service.write_configuration()
    service.execute()


@cli.command()
def grafana():
    service = Grafana()
    service.write_configuration()
    service.execute()


if __name__ == "__main__":
    cli()
