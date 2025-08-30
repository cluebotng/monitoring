import logging
import os
from typing import List, Dict, Optional

import requests
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
app = FastAPI()
RUNNING_TEXT = "Running"
NOT_RUNNING_TEXT = "Not Running"


# Define models for better type safety
class Alert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]


class WebhookPayload(BaseModel):
    status: str
    alerts: List[Alert]


class Wikipedia:
    def __init__(
        self, host: str, page: str, username: Optional[str], password: Optional[str]
    ):
        self.host = host
        self.page = page
        self._session = requests.session()

        if username and password:
            if not self._login(username, password):
                logger.warning(f"Failed to authenticate on {host}")

    def _get_csrf_token(self) -> Optional[str]:
        r = self._session.get(
            f"https://{self.host}/w/api.php",
            headers={
                "User-Agent": "ClueBot NG Monitoring - Wiki Updater",
            },
            params={
                "action": "query",
                "meta": "tokens",
                "type": "csrf",
                "assert": "user",
                "format": "json",
            },
        )
        if r.status_code == 200:
            return r.json().get("query", {}).get("tokens", {}).get("csrftoken")

        logger.warning(
            f"Failed to get CSRF token for {self.host}/{self.page}: [{r.status_code}] {r.text}"
        )
        return None

    def _get_login_token(self) -> Optional[str]:
        r = self._session.get(
            f"https://{self.host}/w/api.php",
            headers={
                "User-Agent": "ClueBot NG Monitoring - Wiki Updater",
            },
            params={
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json",
            },
        )
        if r.status_code == 200:
            return r.json().get("query", {}).get("tokens", {}).get("logintoken")

        logger.warning(
            f"Failed to get LOGIN token for {self.host}/{self.page}: [{r.status_code}] {r.text}"
        )
        return None

    def _login(self, username: str, password: str) -> bool:
        login_token = self._get_login_token()
        if not login_token:
            return False

        r = self._session.post(
            f"https://{self.host}/w/api.php",
            headers={
                "User-Agent": "ClueBot NG Reviewer - Wikipedia - Login",
            },
            data={
                "format": "json",
                "action": "login",
                "lgname": username,
                "lgpassword": password,
                "lgtoken": login_token,
            },
        )
        if r.status_code != 200:
            logger.warning(
                f"Could not login to {self.host}: [{r.status_code}] {r.text}"
            )
            return False

        response = r.json()
        if response.get("login", {}).get("result") != "Success":
            logger.warning(f"Login failed to {self.host}: {response}")
            return False

        return True

    def page_requires_updating(self, running: bool) -> bool:
        r = self._session.get(
            f"https://{self.host}/w/index.php",
            headers={
                "User-Agent": "ClueBot NG Monitoring - Wiki Updater",
            },
            params={
                "title": self.page,
                "action": "raw",
            },
        )
        if r.status_code != 200:
            logger.warning(
                f"Could not fetch {self.host}/{self.page}: [{r.status_code}] {r.text}"
            )
            return False

        expected_text = RUNNING_TEXT if running else NOT_RUNNING_TEXT
        return r.text.strip() != expected_text

    def update_page(self, running: bool) -> bool:
        csrf_token = self._get_csrf_token()
        if not csrf_token:
            return False

        r = self._session.post(
            f"https://{self.host}/w/api.php",
            headers={
                "User-Agent": "ClueBot NG Monitoring - Wiki Updater",
            },
            data={
                "action": "edit",
                "token": csrf_token,
                "format": "json",
                "assert": "user",
                "title": self.page,
                "text": RUNNING_TEXT if running else NOT_RUNNING_TEXT,
                "summary": "Updating status from alerts",
            },
        )

        if r.status_code != 200:
            logger.warning(
                f"Failed to edit {self.host}/{self.page}: [{r.status_code}] {r.text}"
            )
            return False

        return True


@app.post("/alertmanager")
async def alertmanager(payload: WebhookPayload):
    for alert in payload.alerts:
        wiki_host = alert.labels.get("update_wiki_host")
        wiki_page = alert.labels.get("update_wiki_page")
        if not wiki_host or wiki_page:
            logger.info(f"Missing annotations for alert: {alert}")
            continue

        wikipedia = Wikipedia(
            wiki_host,
            wiki_page,
            os.environ.get("WIKI_UPDATER_USERNAME"),
            os.environ.get("WIKI_UPDATER_PASSWORD"),
        )
        is_running = alert.status == "resolved"
        if wikipedia.page_requires_updating(is_running):
            logger.info(f"Updating {wiki_host}/{wiki_page} -> {is_running}")
            if not wikipedia.update_page(is_running):
                logger.error(
                    f"Failed to update {wiki_host}/{wiki_page} -> {is_running}"
                )
        else:
            logger.info(
                f"Page does not require update {wiki_host}/{wiki_page} ({is_running}"
            )

    return "OK"


@app.get("/health")
async def _render_health():
    return "OK"
