import time
from enum import Enum


class InteractionEvent(Enum):
    """the different things the user can 'do' with their eyes/head"""
    NONE = "none"
    ZONE_SELECTED = "zone_selected"   # looked at a zone long enough
    BLINK_CONFIRM = "blink_confirm"   # deliberate long blink
    HEAD_NOD = "head_nod"             # nodded yes
    HEAD_SHAKE = "head_shake"         # shook head no


class GestureEngine:
    """
    takes raw tracker data (gaze, EAR, head angles) and figures out
    what the user is trying to do. handles debouncing so we don't
    get false triggers from normal blinking or small head movements.
    """

    def __init__(self, config):
        interaction = config.get("interaction", {})

        # thresholds from config
        self.blink_threshold = interaction.get("blink_threshold", 0.2)
        self.long_blink_seconds = interaction.get("long_blink_seconds", 0.5)
        self.nod_threshold = interaction.get("nod_threshold", 15)
        self.shake_threshold = interaction.get("shake_threshold", 15)
        self.cooldown_seconds = interaction.get("cooldown_seconds", 3.0)

        # blink tracking
        self._eyes_closed = False
        self._eyes_closed_start = None

        # head gesture tracking - we track the baseline and look for deviations
        self._pitch_history = []
        self._yaw_history = []
        self._history_size = 15  # frames to keep
        self._baseline_pitch = 0.0
        self._baseline_yaw = 0.0
        self._baseline_samples = 0

        # cooldowns to prevent spamming
        self._last_event_time = 0
        self._last_event_type = InteractionEvent.NONE

    def update(self, tracker_result):
        """
        feed in a TrackerResult, get back an InteractionEvent.
        call this every frame.
        """
        if not tracker_result or not tracker_result.face_detected:
            return InteractionEvent.NONE

        now = time.time()

        # check cooldown - don't fire events too fast
        if (now - self._last_event_time) < self.cooldown_seconds:
            # still update tracking state but don't emit events
            self._update_blink_state(tracker_result.ear, now)
            self._update_head_baseline(tracker_result.pitch, tracker_result.yaw)
            return InteractionEvent.NONE

        # check for deliberate blink first (highest priority)
        blink_event = self._check_blink(tracker_result.ear, now)
        if blink_event != InteractionEvent.NONE:
            self._last_event_time = now
            self._last_event_type = blink_event
            return blink_event

        # check head gestures
        head_event = self._check_head_gesture(
            tracker_result.pitch, tracker_result.yaw
        )
        if head_event != InteractionEvent.NONE:
            self._last_event_time = now
            self._last_event_type = head_event
            return head_event

        return InteractionEvent.NONE

    def _check_blink(self, ear, now):
        """detect deliberate long blinks (not normal ones)"""
        if ear < self.blink_threshold:
            # eyes are closed
            if not self._eyes_closed:
                self._eyes_closed = True
                self._eyes_closed_start = now
        else:
            # eyes just opened
            if self._eyes_closed and self._eyes_closed_start:
                closed_duration = now - self._eyes_closed_start
                self._eyes_closed = False
                self._eyes_closed_start = None

                # long enough to be deliberate?
                if closed_duration >= self.long_blink_seconds:
                    return InteractionEvent.BLINK_CONFIRM

            self._eyes_closed = False

        return InteractionEvent.NONE

    def _update_blink_state(self, ear, now):
        """keep tracking blink state even during cooldown"""
        if ear < self.blink_threshold:
            if not self._eyes_closed:
                self._eyes_closed = True
                self._eyes_closed_start = now
        else:
            self._eyes_closed = False
            self._eyes_closed_start = None

    def _update_head_baseline(self, pitch, yaw):
        """keep updating the baseline head position"""
        if self._baseline_samples < 30:
            # still calibrating
            self._baseline_pitch += pitch
            self._baseline_yaw += yaw
            self._baseline_samples += 1
        else:
            # slowly drift the baseline to account for shifting
            self._baseline_pitch = (
                self._baseline_pitch * 0.99 + pitch * 0.01
            )
            self._baseline_yaw = (
                self._baseline_yaw * 0.99 + yaw * 0.01
            )

    def _check_head_gesture(self, pitch, yaw):
        """detect nods and shakes by looking at recent head movement"""

        self._pitch_history.append(pitch)
        self._yaw_history.append(yaw)

        if len(self._pitch_history) > self._history_size:
            self._pitch_history.pop(0)
        if len(self._yaw_history) > self._history_size:
            self._yaw_history.pop(0)

        # update baseline
        self._update_head_baseline(pitch, yaw)

        # need enough samples before we start detecting
        if len(self._pitch_history) < self._history_size:
            return InteractionEvent.NONE

        # check for nod: big pitch change (up-down motion)
        pitch_range = max(self._pitch_history) - min(self._pitch_history)
        if pitch_range > self.nod_threshold:
            self._pitch_history.clear()
            self._yaw_history.clear()
            return InteractionEvent.HEAD_NOD

        # check for shake: big yaw change (left-right motion)
        yaw_range = max(self._yaw_history) - min(self._yaw_history)
        if yaw_range > self.shake_threshold:
            self._pitch_history.clear()
            self._yaw_history.clear()
            return InteractionEvent.HEAD_SHAKE

        return InteractionEvent.NONE

    def reset(self):
        """reset all state"""
        self._eyes_closed = False
        self._eyes_closed_start = None
        self._pitch_history.clear()
        self._yaw_history.clear()
        self._baseline_samples = 0
        self._baseline_pitch = 0.0
        self._baseline_yaw = 0.0
        self._last_event_time = 0
        self._last_event_type = InteractionEvent.NONE
