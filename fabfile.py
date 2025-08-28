import base64

from fabric import Connection, Config, task

c = Connection(
    "login.toolforge.org",
    config=Config(
        overrides={
            "sudo": {
                "user": "tools.cluebotng-monitoring",
                "prefix": "/usr/bin/sudo -ni",
            }
        }
    ),
)


@task()
def setup_webservice(_ctx):
    # Build image
    c.sudo(
        f"XDG_CONFIG_HOME=/data/project/cluebotng-monitoring toolforge build start "
        "-L -i haproxy https://github.com/cluebotng/external-haproxy.git"
    )

    # Ensure the template is setup
    service_template = base64.b64encode(
        (
            "buildservice-image: tool-cluebotng-monitoring/haproxy:latest\n"
            "mount: none\n"
            "health-check-path: /_/health\n"
        ).encode("utf-8")
    ).decode("utf-8")
    c.sudo(
        f"bash -c \"base64 -d <<< '{service_template}' > /data/project/cluebotng-monitoring/service.template\""
    )

    # Restart the web service
    c.sudo(
        f"XDG_CONFIG_HOME=/data/project/cluebotng-monitoring toolforge webservice buildservice restart"
    )
