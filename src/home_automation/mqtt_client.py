import json
import time
import logging

log = logging.getLogger(__name__)

# paho-mqtt is optional
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    log.info("paho-mqtt not installed, mqtt features disabled")


class MQTTClient:
    """
    publishes state change messages so caregivers can monitor
    what the user is doing remotely. also sends help alerts.
    """

    def __init__(self, broker="localhost", port=1883, topic_prefix="home/eyetracker"):
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.client = None
        self.connected = False

    def connect(self):
        if not MQTT_AVAILABLE:
            log.warning("paho-mqtt not installed, can't connect")
            return False

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            log.info(f"connecting to mqtt broker at {self.broker}:{self.port}")
            return True
        except Exception as e:
            log.error(f"mqtt connection failed: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            log.info("mqtt connected")
        else:
            log.error(f"mqtt connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self.connected = False
        log.warning("mqtt disconnected")

    def publish_action(self, zone_name, action, input_method="gaze"):
        """publish a message when user triggers an action"""
        topic = f"{self.topic_prefix}/action"
        payload = {
            "zone": zone_name,
            "action": action,
            "input": input_method,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._publish(topic, payload)

    def publish_state_change(self, item_name, old_state, new_state):
        """publish when a device state changes"""
        topic = f"{self.topic_prefix}/state/{item_name}"
        payload = {
            "item": item_name,
            "old_state": old_state,
            "new_state": new_state,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._publish(topic, payload)

    def publish_alert(self, message="Help requested"):
        """send a help alert for caregivers"""
        topic = f"{self.topic_prefix}/alert"
        payload = {
            "type": "help",
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._publish(topic, payload)
        log.info(f"help alert sent: {message}")

    def _publish(self, topic, payload):
        if not self.client or not self.connected:
            log.debug(f"mqtt not connected, skipping publish to {topic}")
            return

        try:
            self.client.publish(topic, json.dumps(payload), qos=1)
        except Exception as e:
            log.error(f"mqtt publish failed: {e}")

    def disconnect(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
