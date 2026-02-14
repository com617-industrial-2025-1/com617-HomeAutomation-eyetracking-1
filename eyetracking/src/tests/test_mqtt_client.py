"""
unit tests for the mqtt client module.
tests broker connection (mocked) and message publishing.
"""

import unittest
from unittest.mock import patch, MagicMock
from home_automation.mqtt_client import MQTTClient


class TestMQTTClient(unittest.TestCase):

    def setUp(self):
        self.client = MQTTClient(
            broker="localhost",
            port=1883,
            topic_prefix="home/eyetracker"
        )

    def test_init(self):
        self.assertEqual(self.client.broker, "localhost")
        self.assertEqual(self.client.port, 1883)
        self.assertEqual(self.client.topic_prefix, "home/eyetracker")
        self.assertIsNone(self.client.client)

    @patch("home_automation.mqtt_client.mqtt")
    def test_connect_success(self, mock_mqtt):
        mock_mqtt_instance = MagicMock()
        mock_mqtt.Client.return_value = mock_mqtt_instance
        mock_mqtt.CallbackAPIVersion.VERSION2 = "V2"

        with patch("home_automation.mqtt_client.MQTT_AVAILABLE", True):
            self.client.connect()

            self.assertIsNotNone(self.client.client)
            mock_mqtt.Client.assert_called_once_with("V2")
            mock_mqtt_instance.connect.assert_called_once_with("localhost", 1883, keepalive=60)
            mock_mqtt_instance.loop_start.assert_called_once()

    def test_connect_fails_if_not_available(self):
        with patch("home_automation.mqtt_client.MQTT_AVAILABLE", False):
            client = MQTTClient()
            result = client.connect()
            self.assertFalse(result)
            self.assertIsNone(client.client)

    def test_publish_action_not_connected(self):
        # should return early and not crash
        self.client.client = MagicMock()
        self.client.connected = False
        self.client.publish_action("Light", "ON")
        self.client.client.publish.assert_not_called()

    def test_publish_action_connected(self):
        mock_client = MagicMock()
        self.client.client = mock_client
        self.client.connected = True
        
        self.client.publish_action("Light", "ON")

        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        self.assertEqual(args[0], "home/eyetracker/action")
        self.assertIn("Light", args[1])
        self.assertIn("ON", args[1])

    def test_publish_alert_connected(self):
        mock_client = MagicMock()
        self.client.client = mock_client
        self.client.connected = True
        
        self.client.publish_alert("Help me")

        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        self.assertEqual(args[0], "home/eyetracker/alert")
        self.assertIn("Help me", args[1])

    def test_disconnect(self):
        mock_client = MagicMock()
        self.client.client = mock_client
        
        self.client.disconnect()

        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
