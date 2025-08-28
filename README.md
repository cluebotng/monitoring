# ClueBot Monitoring Stack

This is a minimal Prometheus/Alert Manager/Grafana stack for monitoring ClueBot.

The aim is to replace the external perl scripts run on Damian's personal services & the Grafana cloud prometheus setup.

## Testing locally

```
$ pack build --builder heroku/builder:24 monitoring-stack
```

## Production configuration

Expected secrets:

* `TOOL_TOOLSDB_USER` - username to access `tools-db`
* `TOOL_TOOLSDB_PASSWORD` - password to access `tools-db`
