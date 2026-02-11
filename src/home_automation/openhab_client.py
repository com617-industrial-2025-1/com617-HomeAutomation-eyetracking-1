import requests
import logging
import time

log = logging.getLogger(__name__)


class OpenHABClient:
    """talks to openhab's REST API to control devices"""

    def __init__(self, base_url="http://localhost:8080", api_token=None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})

        # cache connection status so we don't spam failed requests
        self._reachable = None
        self._last_check = 0
        self._check_interval = 30  # seconds between recheck attempts
        self._logged_unreachable = False

    def _check_reachable(self):
        """check if openhab is up, cache the result for a while"""
        now = time.time()
        if (now - self._last_check) < self._check_interval:
            return self._reachable

        self._last_check = now
        try:
            resp = self.session.get(f"{self.base_url}/rest/", timeout=1)
            self._reachable = resp.status_code == 200
            if self._reachable:
                self._logged_unreachable = False
                log.info("openhab is reachable")
        except (requests.ConnectionError, requests.Timeout):
            self._reachable = False

        if not self._reachable and not self._logged_unreachable:
            log.warning(f"openhab not reachable at {self.base_url}, will retry in {self._check_interval}s")
            self._logged_unreachable = True

        return self._reachable

    def send_command(self, item_name, command):
        """send a command to an item (e.g. ON, OFF, TOGGLE, 50)"""
        if not self._check_reachable():
            return False

        url = f"{self.base_url}/rest/items/{item_name}"
        try:
            resp = self.session.post(
                url,
                data=command,
                headers={"Content-Type": "text/plain"},
                timeout=2,
            )
            if resp.status_code in (200, 201):
                log.info(f"sent '{command}' to {item_name}")
                return True
            else:
                log.warning(
                    f"openhab returned {resp.status_code} for {item_name}: "
                    f"{resp.text}"
                )
                return False
        except requests.ConnectionError:
            self._reachable = False
            return False
        except requests.Timeout:
            log.error(f"timeout sending to {item_name}")
            return False

    def get_state(self, item_name):
        """get the current state of an item (returns string like 'ON', 'OFF', '75')"""
        url = f"{self.base_url}/rest/items/{item_name}/state"
        try:
            resp = self.session.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.text.strip()
            return None
        except (requests.ConnectionError, requests.Timeout):
            log.error(f"can't get state for {item_name}")
            return None

    def get_all_items(self):
        """get a list of all items from openhab (for LLM context)"""
        url = f"{self.base_url}/rest/items"
        try:
            resp = self.session.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return []
        except (requests.ConnectionError, requests.Timeout):
            log.error("can't fetch items from openhab")
            return []

    def is_connected(self):
        """quick check if openhab is reachable"""
        try:
            resp = self.session.get(
                f"{self.base_url}/rest/", timeout=3
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False
