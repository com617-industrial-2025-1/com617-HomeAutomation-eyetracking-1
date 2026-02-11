import logging

log = logging.getLogger(__name__)

# velbus is optional - only import if available
try:
    import velbus
    VELBUS_AVAILABLE = True
except ImportError:
    VELBUS_AVAILABLE = False
    log.info("python-velbus not installed, velbus features disabled")


class VelbusClient:
    """
    direct serial connection to velbus modules.
    this is the fallback if you're not going through openhab.
    needs a VMB1USB plugged into the pi.
    """

    def __init__(self, serial_port="/dev/ttyACM0", enabled=False):
        self.serial_port = serial_port
        self.enabled = enabled and VELBUS_AVAILABLE
        self.controller = None

    def connect(self):
        if not self.enabled:
            log.info("velbus is disabled in config")
            return False

        if not VELBUS_AVAILABLE:
            log.error("python-velbus package not installed")
            return False

        try:
            self.controller = velbus.Controller(self.serial_port)
            self.controller.scan()
            log.info(f"connected to velbus on {self.serial_port}")
            return True
        except Exception as e:
            log.error(f"failed to connect to velbus: {e}")
            self.controller = None
            return False

    def send_command(self, address, action):
        """
        send a command to a velbus module.
        address: module address on the bus (int)
        action: what to do (e.g. 'ON', 'OFF', 'TOGGLE')
        """
        if not self.controller:
            log.warning("velbus not connected, skipping command")
            return False

        try:
            if action.upper() == "ON":
                msg = velbus.SwitchRelayOnMessage(address)
            elif action.upper() == "OFF":
                msg = velbus.SwitchRelayOffMessage(address)
            else:
                log.warning(f"unknown velbus action: {action}")
                return False

            self.controller.send(msg)
            log.info(f"velbus: sent {action} to address {address}")
            return True
        except Exception as e:
            log.error(f"velbus command failed: {e}")
            return False

    def disconnect(self):
        if self.controller:
            try:
                self.controller.stop()
            except Exception:
                pass
            self.controller = None
