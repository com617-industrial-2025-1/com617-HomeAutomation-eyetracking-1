import cv2
import numpy as np


# colours (BGR)
BG_COLOR = (30, 30, 30)
ZONE_COLOR = (60, 60, 60)
ZONE_ACTIVE_COLOR = (80, 120, 80)
ZONE_TRIGGERED_COLOR = (80, 180, 80)
GAZE_DOT_COLOR = (0, 200, 255)
PROGRESS_COLOR = (0, 255, 200)
TEXT_COLOR = (255, 255, 255)
BORDER_COLOR = (100, 100, 100)
ALERT_COLOR = (0, 0, 255)

# face mesh connections for drawing (subset - just the face outline and eyes)
# these are the tesselation edges used by the old mp.solutions.face_mesh
FACE_OVAL = [
    (10, 338), (338, 297), (297, 332), (332, 284), (284, 251),
    (251, 389), (389, 356), (356, 454), (454, 323), (323, 361),
    (361, 288), (288, 397), (397, 365), (365, 379), (379, 378),
    (378, 400), (400, 377), (377, 152), (152, 148), (148, 176),
    (176, 149), (149, 150), (150, 136), (136, 172), (172, 58),
    (58, 132), (132, 93), (93, 234), (234, 127), (127, 162),
    (162, 21), (21, 54), (54, 103), (103, 67), (67, 109),
    (109, 10),
]

LEFT_EYE_CONTOUR = [
    (362, 382), (382, 381), (381, 380), (380, 374), (374, 373),
    (373, 390), (390, 249), (249, 263), (263, 466), (466, 388),
    (388, 387), (387, 386), (386, 385), (385, 384), (384, 398),
    (398, 362),
]

RIGHT_EYE_CONTOUR = [
    (33, 7), (7, 163), (163, 144), (144, 145), (145, 153),
    (153, 154), (154, 155), (155, 133), (133, 173), (173, 157),
    (157, 158), (158, 159), (159, 160), (160, 161), (161, 246),
    (246, 33),
]


class Overlay:
    """
    draws the UI that the user sees - zones, gaze dot, progress ring,
    and feedback text. designed to be high contrast and easy to read.
    """

    def __init__(self, width=960, height=720):
        self.width = width
        self.height = height

        # feedback messages that fade out
        self._feedback_text = ""
        self._feedback_time = 0
        self._feedback_duration = 2.0

        self._status_text = "ready"

    def draw(self, frame, zones, gaze_x, gaze_y, dwell_progress,
             active_zone, tracker_result=None, triggered_zone=None):
        """draw everything on the frame"""
        if frame is None:
            frame = np.full((self.height, self.width, 3), BG_COLOR, dtype=np.uint8)

        h, w = frame.shape[:2]

        # dim the camera feed so zones stand out
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), BG_COLOR, -1)
        frame = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)

        # draw face mesh if we have landmarks
        if tracker_result and tracker_result.landmarks:
            self._draw_face_mesh(frame, tracker_result, w, h)

        # draw each zone
        for zone in zones:
            self._draw_zone(frame, zone, w, h, active_zone, dwell_progress)

        # gaze dot
        if tracker_result and tracker_result.face_detected:
            gx = int(gaze_x * w)
            gy = int(gaze_y * h)
            cv2.circle(frame, (gx, gy), 12, GAZE_DOT_COLOR, -1)
            cv2.circle(frame, (gx, gy), 14, (255, 255, 255), 2)

        # dwell progress ring on active zone
        if active_zone and dwell_progress > 0:
            self._draw_progress_ring(frame, active_zone, dwell_progress, w, h)

        # triggered confirmation
        if triggered_zone:
            self._set_feedback(f"{triggered_zone.name} activated!")

        # draw feedback text
        self._draw_feedback(frame, w, h)

        # status bar
        self._draw_status_bar(frame, w, h, tracker_result)

        return frame

    def _draw_zone(self, frame, zone, w, h, active_zone, dwell_progress):
        """draw a single zone rectangle with label"""
        x1 = int(zone.x1 * w)
        y1 = int(zone.y1 * h)
        x2 = int(zone.x2 * w)
        y2 = int(zone.y2 * h)

        if zone == active_zone and dwell_progress >= 1.0:
            color = ZONE_TRIGGERED_COLOR
        elif zone == active_zone:
            color = ZONE_ACTIVE_COLOR
        else:
            color = ZONE_COLOR

        zone_overlay = frame.copy()
        cv2.rectangle(zone_overlay, (x1, y1), (x2, y2), color, -1)
        alpha = 0.6
        frame[:] = cv2.addWeighted(zone_overlay, alpha, frame, 1 - alpha, 0)

        # border
        cv2.rectangle(frame, (x1, y1), (x2, y2), BORDER_COLOR, 2)

        # zone label centered
        label = f"{zone.icon} {zone.name}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2

        text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
        text_x = x1 + (x2 - x1 - text_size[0]) // 2
        text_y = y1 + (y2 - y1 + text_size[1]) // 2

        # shadow for readability
        cv2.putText(frame, label, (text_x + 2, text_y + 2), font,
                    font_scale, (0, 0, 0), thickness + 1)
        cv2.putText(frame, label, (text_x, text_y), font,
                    font_scale, TEXT_COLOR, thickness)

    def _draw_progress_ring(self, frame, zone, progress, w, h):
        """circular progress ring in the center of the active zone"""
        cx = int((zone.x1 + zone.x2) / 2 * w)
        cy = int((zone.y1 + zone.y2) / 2 * h)
        radius = 40

        cv2.circle(frame, (cx, cy + 40), radius, (60, 60, 60), 3)

        angle = int(360 * progress)
        cv2.ellipse(frame, (cx, cy + 40), (radius, radius),
                    -90, 0, angle, PROGRESS_COLOR, 4)

    def _draw_face_mesh(self, frame, tracker_result, w, h):
        """draw face outline and eye contours from landmarks"""
        landmarks = tracker_result.landmarks

        # draw face oval
        for start, end in FACE_OVAL:
            pt1 = (int(landmarks[start].x * w), int(landmarks[start].y * h))
            pt2 = (int(landmarks[end].x * w), int(landmarks[end].y * h))
            cv2.line(frame, pt1, pt2, (50, 50, 50), 1)

        # draw eye contours
        for start, end in LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR:
            pt1 = (int(landmarks[start].x * w), int(landmarks[start].y * h))
            pt2 = (int(landmarks[end].x * w), int(landmarks[end].y * h))
            cv2.line(frame, pt1, pt2, (70, 70, 70), 1)

        # draw iris points
        if tracker_result.iris_left:
            cv2.circle(frame, tracker_result.iris_left, 3, (0, 255, 0), -1)
        if tracker_result.iris_right:
            cv2.circle(frame, tracker_result.iris_right, 3, (0, 255, 0), -1)

    def _set_feedback(self, text):
        self._feedback_text = text
        self._feedback_time = cv2.getTickCount() / cv2.getTickFrequency()

    def _draw_feedback(self, frame, w, h):
        if not self._feedback_text:
            return

        now = cv2.getTickCount() / cv2.getTickFrequency()
        elapsed = now - self._feedback_time

        if elapsed > self._feedback_duration:
            self._feedback_text = ""
            return

        alpha = max(0, 1 - (elapsed / self._feedback_duration))
        color = tuple(int(c * alpha) for c in (100, 255, 100))

        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(self._feedback_text, font, 1.2, 2)[0]
        text_x = (w - text_size[0]) // 2
        text_y = 50

        cv2.putText(frame, self._feedback_text, (text_x, text_y), font,
                    1.2, color, 2)

    def _draw_status_bar(self, frame, w, h, tracker_result):
        bar_h = 35
        cv2.rectangle(frame, (0, h - bar_h), (w, h), (20, 20, 20), -1)

        status_parts = []
        if tracker_result and tracker_result.face_detected:
            status_parts.append("face: OK")
            status_parts.append(f"EAR: {tracker_result.ear:.2f}")
            status_parts.append(
                f"head: P{tracker_result.pitch:.0f} "
                f"Y{tracker_result.yaw:.0f}"
            )
        else:
            status_parts.append("no face detected - look at the camera")

        status = " | ".join(status_parts)
        cv2.putText(frame, status, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (150, 150, 150), 1)

    def set_status(self, text):
        self._status_text = text
