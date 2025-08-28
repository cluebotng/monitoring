import asyncio
import logging
from datetime import datetime, UTC, timedelta

import aiohttp
from fastapi import FastAPI, Response
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
    GC_COLLECTOR,
    PROCESS_COLLECTOR,
    PLATFORM_COLLECTOR,
    Gauge,
)

logger = logging.getLogger(__name__)

# Don't run the default collectors
REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)

# Our metrics
last_contribution_time = Gauge(
    "cbng_monitoring_last_contribution_time",
    "Timestamp of the last contribution",
    ["domain", "username"],
)


async def get_latest_edit_time(username: str, domain: str = "en.wikipedia.org") -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{domain}/w/api.php",
            params={
                "action": "query",
                "list": "usercontribs",
                "ucuser": username,
                "uclimit": 1,
                "format": "json",
            },
            headers={"User-Agent": "ClueBot NG Monitoring"},
        ) as r:
            if r.status != 200:
                logger.error(
                    f"Wikipedia API returned non 200 for usercontribs query: {r.status}: {await r.text()}"
                )
                return

            data = await r.json()
            if user_contributions := data.get("query", {}).get("usercontribs", []):
                timestamp = int(
                    datetime.fromisoformat(
                        user_contributions[0]["timestamp"]
                    ).timestamp()
                )
                last_contribution_time.labels(domain=domain, username=username).set(
                    timestamp
                )


app = FastAPI()


class PrometheusResponse(Response):
    media_type = CONTENT_TYPE_LATEST


@app.get("/metrics", response_class=PrometheusResponse)
async def _render_metrics():
    since_time = datetime.now(tz=UTC) - timedelta(hours=24)
    await asyncio.gather(
        get_latest_edit_time("ClueBot III"),
        get_latest_edit_time("ClueBot NG"),
        get_latest_edit_time("ClueBot NG Review Interface"),
    )

    return generate_latest()


@app.get("/health")
async def _render_health():
    return "OK"
