"""
main entry point for the eye tracking home automation system.
run this with: python main.py
"""

import cv2
import yaml
import logging
import sys
import os

# add src to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eye_tracking.tracker import EyeHeadTracker
from eye_tracking.gaze_mapper import GazeMapper
from interaction.gesture_engine import GestureEngine, InteractionEvent
from home_automation.openhab_client import OpenHABClient
from home_automation.velbus_client import VelbusClient
from home_automation.mqtt_client import MQTTClient
from ai.assistant import AIAssistant
from ui.overlay import Overlay

# set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


def load_config(path="config.yaml"):
    """load the yaml config file"""
    config_path = os.path.join(os.path.dirname(__file__), path)
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def handle_zone_trigger(zone, openhab, mqtt, ai_assistant):
    """called when the user activates a zone by staring at it"""

    if zone.alert:
        # help button - send alert to caregiver
        log.info("HELP ALERT triggered!")
        mqtt.publish_alert("Help requested by user")
        return

    if zone.routine:
        # routine zone - let the AI decide what to do
        log.info(f"routine triggered: {zone.name}")
        result = ai_assistant.handle_routine(zone.name)

        for action in result.get("actions", []):
            func = action["function"]
            args = action["args"]

            if func in ("turn_on", "toggle"):
                openhab.send_command(args["item_name"], "ON")
            elif func == "turn_off":
                openhab.send_command(args["item_name"], "OFF")
            elif func == "set_brightness":
                openhab.send_command(
                    args["item_name"], str(args["level"])
                )
            elif func == "set_position":
                openhab.send_command(
                    args["item_name"], args["position"]
                )

        log_msg = result.get("log_message", "routine done")
        mqtt.publish_action(zone.name, log_msg, input_method="gaze")
        log.info(f"routine result: {log_msg}")
        return

    # normal zone - just send the command directly
    if zone.item and zone.command:
        log.info(f"sending {zone.command} to {zone.item}")
        openhab.send_command(zone.item, zone.command)
        mqtt.publish_action(zone.name, zone.command, input_method="gaze")


def main():
    config = load_config()

    # init everything
    tracker = EyeHeadTracker(
        camera_index=config.get("camera", {}).get("index", 0)
    )
    gaze_mapper = GazeMapper(
        zones_config=config["zones"],
        dwell_time_seconds=config.get("interaction", {}).get(
            "dwell_time_seconds", 2.0
        ),
    )
    gesture_engine = GestureEngine(config)

    openhab_config = config.get("openhab", {})
    openhab = OpenHABClient(
        base_url=openhab_config.get("base_url", "http://localhost:8080"),
        api_token=openhab_config.get("api_token"),
    )

    velbus_config = config.get("velbus", {})
    velbus = VelbusClient(
        serial_port=velbus_config.get("serial_port", "/dev/ttyACM0"),
        enabled=velbus_config.get("enabled", False),
    )

    mqtt_config = config.get("mqtt", {})
    mqtt = MQTTClient(
        broker=mqtt_config.get("broker", "localhost"),
        port=mqtt_config.get("port", 1883),
        topic_prefix=mqtt_config.get("topic_prefix", "home/eyetracker"),
    )

    ai_config = config.get("ai", {})
    ai_assistant = AIAssistant(
        api_key=ai_config.get("gemini_api_key"),
        model=ai_config.get("model", "gemini-2.0-flash"),
    )

    overlay = Overlay()

    # start connections
    log.info("starting eye tracker...")
    tracker.start()
    mqtt.connect()

    if velbus_config.get("enabled", False):
        velbus.connect()

    cooldown = config.get("interaction", {}).get("cooldown_seconds", 3.0)

    log.info("system ready - press Esc to quit")

    triggered_zone = None

    try:
        while True:
            # grab frame and track
            frame, tracker_result = tracker.process_frame()
            if frame is None:
                break

            # map gaze to zones
            gaze_result = {"zone": None, "dwell_progress": 0, "triggered": False}
            if tracker_result and tracker_result.face_detected:
                gaze_result = gaze_mapper.update(
                    tracker_result.gaze_x,
                    tracker_result.gaze_y,
                    cooldown_seconds=cooldown,
                )

            # check for gestures (blink, nod, shake)
            gesture = gesture_engine.update(tracker_result)

            # handle zone trigger via dwell
            triggered_zone = None
            if gaze_result["triggered"]:
                triggered_zone = gaze_result["zone"]
                handle_zone_trigger(
                    triggered_zone, openhab, mqtt, ai_assistant
                )

            # handle blink confirmation on active zone
            if (gesture == InteractionEvent.BLINK_CONFIRM and
                    gaze_result["zone"] is not None):
                triggered_zone = gaze_result["zone"]
                handle_zone_trigger(
                    triggered_zone, openhab, mqtt, ai_assistant
                )

            # draw the UI
            frame = overlay.draw(
                frame=frame,
                zones=gaze_mapper.zones,
                gaze_x=tracker_result.gaze_x if tracker_result else 0.5,
                gaze_y=tracker_result.gaze_y if tracker_result else 0.5,
                dwell_progress=gaze_result["dwell_progress"],
                active_zone=gaze_result["zone"],
                tracker_result=tracker_result,
                triggered_zone=triggered_zone,
            )

            cv2.imshow("Eye Tracking Home Control", frame)

            # esc to quit
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        log.info("interrupted by user")

    finally:
        log.info("shutting down...")
        tracker.stop()
        mqtt.disconnect()
        velbus.disconnect()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
