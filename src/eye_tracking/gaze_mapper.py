import time


class Zone:
    """a clickable zone on screen - maps to a device or action"""

    def __init__(self, name, icon, region, item=None, command=None,
                 routine=False, alert=False):
        self.name = name
        self.icon = icon
        self.x1, self.y1, self.x2, self.y2 = region
        self.item = item        # openhab item name
        self.command = command   # e.g. TOGGLE, ON, OFF
        self.routine = routine   # triggers a multi-step routine via LLM
        self.alert = alert       # sends help alert to caregiver

    def contains(self, gaze_x, gaze_y):
        return (self.x1 <= gaze_x <= self.x2 and
                self.y1 <= gaze_y <= self.y2)

    def __repr__(self):
        return f"Zone({self.icon} {self.name})"


class GazeMapper:
    """tracks which zone the user is looking at and for how long"""

    def __init__(self, zones_config, dwell_time_seconds=2.0):
        self.zones = []
        for z in zones_config:
            self.zones.append(Zone(
                name=z["name"],
                icon=z.get("icon", "⬜"),
                region=z["region"],
                item=z.get("item"),
                command=z.get("command"),
                routine=z.get("routine", False),
                alert=z.get("alert", False),
            ))

        self.dwell_time = dwell_time_seconds

        self._current_zone = None
        self._dwell_start = None
        self._last_triggered_zone = None
        self._last_trigger_time = 0

    def update(self, gaze_x, gaze_y, cooldown_seconds=3.0):
        """
        call this every frame with the current gaze position.
        returns which zone they're on, how long they've been looking (0-1),
        and whether it just triggered.
        """
        now = time.time()

        # check which zone they're looking at
        active_zone = None
        for zone in self.zones:
            if zone.contains(gaze_x, gaze_y):
                active_zone = zone
                break

        # if they moved to a different zone, reset the timer
        if active_zone != self._current_zone:
            self._current_zone = active_zone
            self._dwell_start = now if active_zone else None

        dwell_progress = 0.0
        triggered = False

        if active_zone and self._dwell_start:
            elapsed = now - self._dwell_start
            dwell_progress = min(1.0, elapsed / self.dwell_time)

            # dwell completed - fire the action
            if dwell_progress >= 1.0:
                # cooldown so it doesn't keep firing repeatedly
                if (self._last_triggered_zone != active_zone or
                        (now - self._last_trigger_time) > cooldown_seconds):
                    triggered = True
                    self._last_triggered_zone = active_zone
                    self._last_trigger_time = now

                self._dwell_start = now

        return {
            "zone": active_zone,
            "dwell_progress": dwell_progress,
            "triggered": triggered,
        }

    def reset(self):
        self._current_zone = None
        self._dwell_start = None
        self._last_triggered_zone = None
        self._last_trigger_time = 0
