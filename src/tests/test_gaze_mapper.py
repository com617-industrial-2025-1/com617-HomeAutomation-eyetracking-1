"""
unit tests for the gaze mapper module.
tests zone detection, dwell timing, and look-away reset.
"""

import unittest
import time
from unittest.mock import patch
from eye_tracking.gaze_mapper import GazeMapper, Zone


# test zone config matching config.yaml layout
TEST_ZONES = [
    {"name": "Light", "icon": "[LIGHT]", "region": [0.0, 0.0, 0.5, 0.5],
     "item": "LivingRoom_Light", "command": "TOGGLE"},
    {"name": "Blinds", "icon": "[BLINDS]", "region": [0.5, 0.0, 1.0, 0.5],
     "item": "Bedroom_Blinds", "command": "UP"},
    {"name": "Bedtime", "icon": "[SLEEP]", "region": [0.0, 0.5, 0.5, 1.0],
     "routine": True},
    {"name": "Help", "icon": "[SOS]", "region": [0.5, 0.5, 1.0, 1.0],
     "alert": True},
]


class TestZone(unittest.TestCase):

    def test_zone_contains_center(self):
        zone = Zone("Test", "T", [0.0, 0.0, 0.5, 0.5])
        self.assertTrue(zone.contains(0.25, 0.25))

    def test_zone_contains_edge(self):
        zone = Zone("Test", "T", [0.0, 0.0, 0.5, 0.5])
        self.assertTrue(zone.contains(0.0, 0.0))
        self.assertTrue(zone.contains(0.5, 0.5))

    def test_zone_outside(self):
        zone = Zone("Test", "T", [0.0, 0.0, 0.5, 0.5])
        self.assertFalse(zone.contains(0.6, 0.6))
        self.assertFalse(zone.contains(0.75, 0.25))

    def test_zone_repr(self):
        zone = Zone("Light", "[LIGHT]", [0.0, 0.0, 0.5, 0.5])
        self.assertEqual(repr(zone), "Zone([LIGHT] Light)")


class TestGazeMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = GazeMapper(TEST_ZONES, dwell_time_seconds=1.0)

    def test_zones_created(self):
        self.assertEqual(len(self.mapper.zones), 4)
        self.assertEqual(self.mapper.zones[0].name, "Light")
        self.assertEqual(self.mapper.zones[1].name, "Blinds")

    def test_zone_properties(self):
        light = self.mapper.zones[0]
        self.assertEqual(light.item, "LivingRoom_Light")
        self.assertEqual(light.command, "TOGGLE")
        self.assertFalse(light.routine)
        self.assertFalse(light.alert)

        bedtime = self.mapper.zones[2]
        self.assertTrue(bedtime.routine)

        help_zone = self.mapper.zones[3]
        self.assertTrue(help_zone.alert)

    def test_gaze_maps_to_correct_zone(self):
        # top-left = Light
        result = self.mapper.update(0.25, 0.25)
        self.assertEqual(result["zone"].name, "Light")

        # top-right = Blinds
        self.mapper.reset()
        result = self.mapper.update(0.75, 0.25)
        self.assertEqual(result["zone"].name, "Blinds")

        # bottom-left = Bedtime
        self.mapper.reset()
        result = self.mapper.update(0.25, 0.75)
        self.assertEqual(result["zone"].name, "Bedtime")

        # bottom-right = Help
        self.mapper.reset()
        result = self.mapper.update(0.75, 0.75)
        self.assertEqual(result["zone"].name, "Help")

    def test_gaze_outside_all_zones(self):
        # outside any valid region shouldn't happen with full coverage
        # but test the boundary
        result = self.mapper.update(0.5, 0.5)
        # 0.5, 0.5 is on the border of all 4 zones, should match Light
        self.assertIsNotNone(result["zone"])

    def test_dwell_progress_builds(self):
        # first frame: just started dwelling
        result = self.mapper.update(0.25, 0.25)
        self.assertEqual(result["dwell_progress"], 0.0)
        self.assertFalse(result["triggered"])

    @patch("time.time")
    def test_dwell_triggers_after_threshold(self, mock_time):
        mock_time.return_value = 100.0
        self.mapper.update(0.25, 0.25)  # start dwell

        mock_time.return_value = 101.5  # 1.5s later (> 1.0s threshold)
        result = self.mapper.update(0.25, 0.25)
        self.assertTrue(result["triggered"])
        self.assertGreaterEqual(result["dwell_progress"], 1.0)

    @patch("time.time")
    def test_look_away_resets_trigger(self, mock_time):
        # dwell on Light until triggered
        mock_time.return_value = 100.0
        self.mapper.update(0.25, 0.25)
        mock_time.return_value = 101.5
        result = self.mapper.update(0.25, 0.25)
        self.assertTrue(result["triggered"])

        # still looking at Light - should NOT trigger again
        mock_time.return_value = 103.0
        result = self.mapper.update(0.25, 0.25)
        self.assertFalse(result["triggered"])

        # look away to Blinds
        mock_time.return_value = 104.0
        self.mapper.update(0.75, 0.25)

        # look back at Light - should be able to trigger again
        mock_time.return_value = 105.0
        self.mapper.update(0.25, 0.25)
        mock_time.return_value = 106.5
        result = self.mapper.update(0.25, 0.25)
        self.assertTrue(result["triggered"])

    def test_reset(self):
        self.mapper.update(0.25, 0.25)
        self.mapper.reset()
        self.assertIsNone(self.mapper._current_zone)
        self.assertIsNone(self.mapper._dwell_start)
        self.assertFalse(self.mapper._awaiting_look_away)


if __name__ == "__main__":
    unittest.main()
