"""
unit tests for the openhab client module.
tests REST API calls, auth headers, and reachability caching.
"""

import unittest
import time
from unittest.mock import patch, MagicMock
from home_automation.openhab_client import OpenHABClient


class TestOpenHABClientInit(unittest.TestCase):

    def test_default_base_url(self):
        client = OpenHABClient()
        self.assertEqual(client.base_url, "http://localhost:8080")

    def test_custom_base_url(self):
        client = OpenHABClient(base_url="http://192.168.1.100:9090/")
        self.assertEqual(client.base_url, "http://192.168.1.100:9090")

    def test_trailing_slash_stripped(self):
        client = OpenHABClient(base_url="http://localhost:8080/")
        self.assertEqual(client.base_url, "http://localhost:8080")

    def test_api_token_sets_auth_header(self):
        client = OpenHABClient(api_token="oh.test.abc123")
        self.assertEqual(
            client.session.headers["Authorization"],
            "Bearer oh.test.abc123"
        )

    def test_no_token_no_auth_header(self):
        client = OpenHABClient()
        self.assertNotIn("Authorization", client.session.headers)

    def test_accept_header_set(self):
        client = OpenHABClient()
        self.assertEqual(client.session.headers["Accept"], "application/json")


class TestOpenHABClientReachability(unittest.TestCase):

    def test_reachable_when_server_responds(self):
        client = OpenHABClient(api_token="test")
        # mock the session.get to return 200
        client.session.get = MagicMock(
            return_value=MagicMock(status_code=200)
        )
        client._last_check = 0  # force recheck
        result = client._check_reachable()
        self.assertTrue(result)
        self.assertTrue(client._reachable)

    def test_unreachable_when_connection_fails(self):
        import requests
        client = OpenHABClient(api_token="test")
        client.session.get = MagicMock(
            side_effect=requests.ConnectionError("refused")
        )
        client._last_check = 0
        result = client._check_reachable()
        self.assertFalse(result)
        self.assertFalse(client._reachable)

    def test_reachability_cached(self):
        client = OpenHABClient(api_token="test")
        client._reachable = True
        client._last_check = time.time()  # just checked

        # should return cached value without calling get
        client.session.get = MagicMock()
        result = client._check_reachable()
        self.assertTrue(result)
        client.session.get.assert_not_called()


class TestOpenHABClientCommands(unittest.TestCase):

    def _make_client(self):
        client = OpenHABClient(api_token="oh.test.token")
        client._reachable = True
        client._last_check = time.time()
        return client

    def test_send_command_url_format(self):
        client = self._make_client()
        client.session.post = MagicMock(
            return_value=MagicMock(status_code=200)
        )
        client.send_command("LivingRoom_Light", "ON")

        client.session.post.assert_called_once()
        url = client.session.post.call_args[0][0]
        self.assertIn("LivingRoom_Light", url)
        self.assertIn("/rest/items/", url)

    def test_send_command_data(self):
        client = self._make_client()
        client.session.post = MagicMock(
            return_value=MagicMock(status_code=200)
        )
        client.send_command("Bedroom_Blinds", "UP")

        call_kwargs = client.session.post.call_args
        # command should be in the request body
        self.assertIn("UP", str(call_kwargs))

    def test_get_state_url_format(self):
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.text = "ON"
        mock_resp.status_code = 200
        client.session.get = MagicMock(return_value=mock_resp)

        state = client.get_state("LivingRoom_Light")

        # should have been called (once for getting state)
        self.assertTrue(client.session.get.called)

    def test_send_command_skips_when_unreachable(self):
        client = self._make_client()
        client._reachable = False
        client.session.post = MagicMock()

        result = client.send_command("LivingRoom_Light", "ON")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
