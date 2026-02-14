import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    FaceLandmarker,
    FaceLandmarkerOptions,
    RunningMode,
)
import os

# landmark indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

# nose tip for face center reference
NOSE_TIP = 1

# face width reference points (left and right cheek/temple area)
FACE_LEFT = 234   # right temple (appears left in flipped image)
FACE_RIGHT = 454  # left temple (appears right in flipped image)
FACE_TOP = 10     # forehead
FACE_BOTTOM = 152 # chin


class TrackerResult:
    def __init__(self):
        self.face_detected = False
        self.gaze_x = 0.5
        self.gaze_y = 0.5
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        self.left_ear = 0.0
        self.right_ear = 0.0
        self.ear = 0.0
        self.blink_detected = False
        self.landmarks = None
        self.iris_left = None
        self.iris_right = None


class EyeHeadTracker:
    """handles mediapipe face landmarker - gets gaze, head angle, and blinks"""

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "face_landmarker.task"
        )
        model_path = os.path.normpath(model_path)

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.IMAGE,
            num_faces=1,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = FaceLandmarker.create_from_options(options)

        # exponential smoothing for fluid gaze movement
        # lower alpha = smoother but slower to respond
        self._smooth_alpha = 0.15
        self._smooth_x = 0.5
        self._smooth_y = 0.5
        self._initialized = False

        self._frame_w = 0
        self._frame_h = 0

    def start(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera at index {self.camera_index}. "
                "Check the camera connection."
            )
        self._frame_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._frame_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def stop(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.landmarker.close()

    def process_frame(self):
        """grab a frame, run face landmarker, return (frame, TrackerResult)"""
        if not self.cap or not self.cap.isOpened():
            return None, None

        ret, frame = self.cap.read()
        if not ret:
            return None, None

        frame = cv2.flip(frame, 1)
        result = TrackerResult()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection = self.landmarker.detect(mp_image)

        if not detection.face_landmarks:
            return frame, result

        landmarks = detection.face_landmarks[0]
        result.face_detected = True
        result.landmarks = landmarks

        h, w = frame.shape[:2]

        if len(landmarks) > 477:
            result.iris_left = self._get_iris_center(landmarks, LEFT_IRIS, w, h)
            result.iris_right = self._get_iris_center(landmarks, RIGHT_IRIS, w, h)
            gaze_x, gaze_y = self._calculate_gaze(landmarks)
            result.gaze_x = gaze_x
            result.gaze_y = gaze_y

        # head angle (simplified - just use face landmarks directly)
        result.pitch, result.yaw, result.roll = self._estimate_head_pose_simple(landmarks)

        # blink check
        result.left_ear = self._calculate_ear(landmarks, LEFT_EYE, w, h)
        result.right_ear = self._calculate_ear(landmarks, RIGHT_EYE, w, h)
        result.ear = (result.left_ear + result.right_ear) / 2.0

        return frame, result

    def _get_iris_center(self, landmarks, iris_indices, w, h):
        points = []
        for idx in iris_indices:
            lm = landmarks[idx]
            points.append((int(lm.x * w), int(lm.y * h)))
        cx = int(np.mean([p[0] for p in points]))
        cy = int(np.mean([p[1] for p in points]))
        return (cx, cy)

    def _calculate_gaze(self, landmarks):
        """
        simple and reliable gaze calculation:
        - measure where the avg iris center sits relative to the face bounding box
        - iris shifts left/right/up/down within the face as you look around
        - also factor in head position (looking left = head turns left)
        """
        def lm_x(idx):
            return landmarks[idx].x

        def lm_y(idx):
            return landmarks[idx].y

        # average iris position
        iris_x = np.mean([lm_x(i) for i in LEFT_IRIS + RIGHT_IRIS])
        iris_y = np.mean([lm_y(i) for i in LEFT_IRIS + RIGHT_IRIS])

        # face bounding box from key landmarks
        face_left = lm_x(FACE_LEFT)
        face_right = lm_x(FACE_RIGHT)
        face_top = lm_y(FACE_TOP)
        face_bottom = lm_y(FACE_BOTTOM)

        face_w = face_right - face_left
        face_h = face_bottom - face_top

        if face_w < 0.01 or face_h < 0.01:
            return 0.5, 0.5

        # where is the iris inside the face box? (0 = left edge, 1 = right edge)
        raw_x = (iris_x - face_left) / face_w
        raw_y = (iris_y - face_top) / face_h

        # stretch iris range to fill [0, 1] for more sensitivity
        # vertical range is tighter (0.30-0.55) because looking down is limited by eyelids
        gaze_x = self._expand(raw_x, 0.25, 0.75)
        gaze_y = self._expand(raw_y, 0.30, 0.55)

        # factor in head position - when you look left, your whole head
        # shifts left in the frame. use nose position as head indicator.
        nose_x = lm_x(NOSE_TIP)
        head_offset_x = (nose_x - 0.5) * 1.5
        # stronger vertical head contribution - helps reach bottom zones
        head_offset_y = (lm_y(NOSE_TIP) - 0.40) * 2.0

        gaze_x = gaze_x * 0.5 + (0.5 + head_offset_x) * 0.5
        # give more weight to head tilt for vertical (60%) since eyes alone can't look far down
        gaze_y = gaze_y * 0.4 + (0.5 + head_offset_y) * 0.6

        # smooth for fluid movement
        gaze_x = self._smooth(gaze_x, 'x')
        gaze_y = self._smooth(gaze_y, 'y')

        return max(0.0, min(1.0, gaze_x)), max(0.0, min(1.0, gaze_y))

    def _expand(self, value, low, high):
        """stretch value from [low, high] range to [0, 1]"""
        if high <= low:
            return 0.5
        return max(0.0, min(1.0, (value - low) / (high - low)))

    def _smooth(self, value, axis):
        """exponential moving average - gives fluid cursor movement"""
        if not self._initialized:
            self._smooth_x = value if axis == 'x' else self._smooth_x
            self._smooth_y = value if axis == 'y' else self._smooth_y
            self._initialized = True
            return value

        if axis == 'x':
            self._smooth_x = self._smooth_alpha * value + (1 - self._smooth_alpha) * self._smooth_x
            return self._smooth_x
        else:
            self._smooth_y = self._smooth_alpha * value + (1 - self._smooth_alpha) * self._smooth_y
            return self._smooth_y

    def _estimate_head_pose_simple(self, landmarks):
        """
        simple head pose from face landmarks, no solvePnP needed.
        - yaw: nose x relative to face center (left/right)
        - pitch: nose y relative to face center (up/down)
        - roll: angle between eye centers (tilt)
        """
        nose = landmarks[NOSE_TIP]
        face_left = landmarks[FACE_LEFT]
        face_right = landmarks[FACE_RIGHT]

        # yaw: where is the nose between left and right face edges?
        face_w = face_right.x - face_left.x
        if face_w > 0.01:
            nose_ratio = (nose.x - face_left.x) / face_w
            yaw = (nose_ratio - 0.5) * 60  # scale to roughly -30 to +30 degrees
        else:
            yaw = 0

        # pitch: nose height relative to face vertical center
        face_top = landmarks[FACE_TOP]
        face_bottom = landmarks[FACE_BOTTOM]
        face_h = face_bottom.y - face_top.y
        if face_h > 0.01:
            nose_v_ratio = (nose.y - face_top.y) / face_h
            pitch = (nose_v_ratio - 0.55) * 60
        else:
            pitch = 0

        # roll: angle between the two eye centers
        left_eye_center = np.mean([landmarks[i].x for i in LEFT_IRIS]), np.mean([landmarks[i].y for i in LEFT_IRIS])
        right_eye_center = np.mean([landmarks[i].x for i in RIGHT_IRIS]), np.mean([landmarks[i].y for i in RIGHT_IRIS])
        dx = right_eye_center[0] - left_eye_center[0]
        dy = right_eye_center[1] - left_eye_center[1]
        roll = np.degrees(np.arctan2(dy, dx))

        return pitch, yaw, roll

    def _calculate_ear(self, landmarks, eye_indices, w, h):
        """eye aspect ratio - drops to ~0 when the eye closes"""
        def get_point(idx):
            lm = landmarks[idx]
            return np.array([lm.x * w, lm.y * h])

        p1 = get_point(eye_indices[0])
        p2 = get_point(eye_indices[1])
        p3 = get_point(eye_indices[2])
        p4 = get_point(eye_indices[3])
        p5 = get_point(eye_indices[4])
        p6 = get_point(eye_indices[5])

        vertical_1 = np.linalg.norm(p2 - p6)
        vertical_2 = np.linalg.norm(p3 - p5)
        horizontal = np.linalg.norm(p1 - p4)

        if horizontal < 1e-6:
            return 0.0

        return (vertical_1 + vertical_2) / (2.0 * horizontal)
