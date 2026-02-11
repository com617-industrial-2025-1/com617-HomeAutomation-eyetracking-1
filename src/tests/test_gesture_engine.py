"""
unit tests for the gesture engine module.
tests blink detection, head gestures, and cooldown periods.
"""

import unittest
from unittest.mock import MagicMock, patch
from interaction.gesture_engine import GestureEngine, InteractionEvent


def make_config(blink_thresh=0.2, long_blink=0.5, nod_thresh=15, shake_thresh=15):
    return {
        "interaction": {
            "blink_threshold": blink_thresh,
            "long_blink_seconds": long_blink,
            "nod_threshold": nod_thresh,
            "shake_threshold": shake_thresh,
        }
    }


def make_tracker_result(ear=0.3, pitch=0.0, yaw=0.0, face_detected=True):
    result = MagicMock()
    result.face_detected = face_detected
    result.ear = ear
    result.left_ear = ear
    result.right_ear = ear
    result.pitch = pitch
    result.yaw = yaw
    result.roll = 0.0
    return result


class TestGestureEngine(unittest.TestCase):

    def setUp(self):
        self.engine = GestureEngine(make_config())

    def test_no_face_returns_none(self):
        result = self.engine.update(make_tracker_result(face_detected=False))
        self.assertEqual(result, InteractionEvent.NONE)

    def test_normal_ear_no_event(self):
        result = self.engine.update(make_tracker_result(ear=0.3))
        self.assertEqual(result, InteractionEvent.NONE)

    def test_eyes_closed_no_immediate_event(self):
        result = self.engine.update(make_tracker_result(ear=0.1))
        self.assertEqual(result, InteractionEvent.NONE)

    @patch("interaction.gesture_engine.time")
    def test_long_blink_triggers_confirm(self, mock_time):
        engine = GestureEngine(make_config(long_blink=0.5))

        # eyes open - build baseline
        mock_time.time.return_value = 100.0
        for _ in range(5):
            engine.update(make_tracker_result(ear=0.3))

        # eyes close
        mock_time.time.return_value = 101.0
        engine.update(make_tracker_result(ear=0.1))

        # eyes open after 0.6s (longer than 0.5s threshold)
        mock_time.time.return_value = 101.6
        result = engine.update(make_tracker_result(ear=0.3))
        self.assertEqual(result, InteractionEvent.BLINK_CONFIRM)

    def test_head_at_rest_no_gesture(self):
        result = self.engine.update(make_tracker_result(pitch=0.0, yaw=0.0))
        self.assertEqual(result, InteractionEvent.NONE)

    def test_config_values_loaded(self):
        config = make_config(blink_thresh=0.15, nod_thresh=20)
        engine = GestureEngine(config)
        self.assertEqual(engine.blink_threshold, 0.15)
        self.assertEqual(engine.nod_threshold, 20)

    def test_none_tracker_result(self):
        result = self.engine.update(None)
        self.assertEqual(result, InteractionEvent.NONE)

    def test_reset_clears_state(self):
        self.engine.update(make_tracker_result(ear=0.1))
        self.engine.reset()
        self.assertFalse(self.engine._eyes_closed)
        self.assertIsNone(self.engine._eyes_closed_start)
        self.assertEqual(len(self.engine._pitch_history), 0)


class TestInteractionEvent(unittest.TestCase):

    def test_event_values(self):
        self.assertEqual(InteractionEvent.BLINK_CONFIRM.value, "blink_confirm")
        self.assertEqual(InteractionEvent.HEAD_NOD.value, "head_nod")
        self.assertEqual(InteractionEvent.HEAD_SHAKE.value, "head_shake")
        self.assertEqual(InteractionEvent.NONE.value, "none")


if __name__ == "__main__":
    unittest.main()
