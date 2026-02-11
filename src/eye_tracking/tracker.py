import cv2
import numpy as np
import mediapipe as mp
import time

# landmark indices we need for eye/iris/face tracking
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
# nose tip, chin, eye corners, mouth corners - used for head pose
FACE_POSE_LANDMARKS = [1, 152, 33, 263, 61, 291]


class TrackerResult:
    """holds tracking data for a single frame"""

    def __init__(self):
        self.face_detected = False
        self.gaze_x = 0.5
        self.gaze_y = 0.5
        self.pitch = 0.0   # up/down (nod)
        self.yaw = 0.0     # left/right (shake)
        self.roll = 0.0    # head tilt
        self.left_ear = 0.0
        self.right_ear = 0.0
        self.ear = 0.0     # avg eye aspect ratio
        self.blink_detected = False
        self.landmarks = None
        self.iris_left = None
        self.iris_right = None


class EyeHeadTracker:
    """handles all the mediapipe face mesh stuff - gets gaze, head angle, and blinks"""

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

        # face mesh with iris tracking turned on
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # rolling average to stop the gaze jumping around
        self._gaze_buffer_x = []
        self._gaze_buffer_y = []
        self._buffer_size = 5

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
        self.face_mesh.close()

    def process_frame(self):
        """grab a frame, run face mesh, return (frame, TrackerResult)"""
        if not self.cap or not self.cap.isOpened():
            return None, None

        ret, frame = self.cap.read()
        if not ret:
            return None, None

        # mirror the image so it feels natural
        frame = cv2.flip(frame, 1)
        result = TrackerResult()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_results = self.face_mesh.process(rgb_frame)

        if not mp_results.multi_face_landmarks:
            return frame, result

        face_landmarks = mp_results.multi_face_landmarks[0]
        result.face_detected = True
        result.landmarks = face_landmarks

        h, w = frame.shape[:2]

        # work out where they're looking
        result.iris_left = self._get_iris_center(face_landmarks, LEFT_IRIS, w, h)
        result.iris_right = self._get_iris_center(face_landmarks, RIGHT_IRIS, w, h)
        gaze_x, gaze_y = self._calculate_gaze(face_landmarks, w, h)
        result.gaze_x = gaze_x
        result.gaze_y = gaze_y

        # head angle
        pitch, yaw, roll = self._estimate_head_pose(face_landmarks, w, h)
        result.pitch = pitch
        result.yaw = yaw
        result.roll = roll

        # blink check
        result.left_ear = self._calculate_ear(face_landmarks, LEFT_EYE, w, h)
        result.right_ear = self._calculate_ear(face_landmarks, RIGHT_EYE, w, h)
        result.ear = (result.left_ear + result.right_ear) / 2.0

        return frame, result

    def _get_iris_center(self, landmarks, iris_indices, w, h):
        """average the iris landmark positions to get the center point"""
        points = []
        for idx in iris_indices:
            lm = landmarks.landmark[idx]
            points.append((int(lm.x * w), int(lm.y * h)))
        cx = int(np.mean([p[0] for p in points]))
        cy = int(np.mean([p[1] for p in points]))
        return (cx, cy)

    def _calculate_gaze(self, landmarks, w, h):
        """figure out gaze as 0-1 coords based on where the iris sits inside the eye"""

        def get_point(idx):
            lm = landmarks.landmark[idx]
            return np.array([lm.x * w, lm.y * h])

        # left eye iris vs eye corners
        left_iris = np.mean([get_point(i) for i in LEFT_IRIS], axis=0)
        left_inner = get_point(362)
        left_outer = get_point(263)

        # right eye iris vs eye corners
        right_iris = np.mean([get_point(i) for i in RIGHT_IRIS], axis=0)
        right_inner = get_point(133)
        right_outer = get_point(33)

        # horizontal: where is the iris between the two corners?
        left_ratio_x = self._point_ratio(left_iris[0], left_outer[0], left_inner[0])
        right_ratio_x = self._point_ratio(right_iris[0], right_outer[0], right_inner[0])
        gaze_x = (left_ratio_x + right_ratio_x) / 2.0

        # vertical: same idea but top-to-bottom of the eye
        left_top = get_point(385)
        left_bottom = get_point(380)
        right_top = get_point(160)
        right_bottom = get_point(144)

        left_ratio_y = self._point_ratio(left_iris[1], left_top[1], left_bottom[1])
        right_ratio_y = self._point_ratio(right_iris[1], right_top[1], right_bottom[1])
        gaze_y = (left_ratio_y + right_ratio_y) / 2.0

        # smooth it out and clamp
        gaze_x = self._smooth_value(gaze_x, self._gaze_buffer_x)
        gaze_y = self._smooth_value(gaze_y, self._gaze_buffer_y)
        gaze_x = max(0.0, min(1.0, gaze_x))
        gaze_y = max(0.0, min(1.0, gaze_y))

        return gaze_x, gaze_y

    def _point_ratio(self, value, start, end):
        """where does 'value' sit between start and end? returns 0-1"""
        denom = end - start
        if abs(denom) < 1e-6:
            return 0.5
        return (value - start) / denom

    def _smooth_value(self, value, buffer):
        """simple moving average to reduce jitter"""
        buffer.append(value)
        if len(buffer) > self._buffer_size:
            buffer.pop(0)
        return sum(buffer) / len(buffer)

    def _estimate_head_pose(self, landmarks, w, h):
        """uses solvePnP to get pitch/yaw/roll from face landmarks"""

        # generic 3d face model points
        model_points = np.array([
            [0.0, 0.0, 0.0],          # nose tip
            [0.0, -330.0, -65.0],      # chin
            [-225.0, 170.0, -135.0],   # left eye corner
            [225.0, 170.0, -135.0],    # right eye corner
            [-150.0, -150.0, -125.0],  # left mouth corner
            [150.0, -150.0, -125.0],   # right mouth corner
        ], dtype=np.float64)

        # where those points are in the actual image
        image_points = np.array([
            self._lm_to_pixel(landmarks, idx, w, h)
            for idx in FACE_POSE_LANDMARKS
        ], dtype=np.float64)

        # rough camera matrix based on frame size
        focal_length = w
        center = (w / 2.0, h / 2.0)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)

        dist_coeffs = np.zeros((4, 1))

        success, rotation_vec, _ = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return 0.0, 0.0, 0.0

        # convert rotation to euler angles
        rotation_mat, _ = cv2.Rodrigues(rotation_vec)
        pose_mat = np.hstack((rotation_mat, np.zeros((3, 1))))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)

        pitch = euler_angles[0][0]
        yaw = euler_angles[1][0]
        roll = euler_angles[2][0]

        return pitch, yaw, roll

    def _lm_to_pixel(self, landmarks, idx, w, h):
        lm = landmarks.landmark[idx]
        return [lm.x * w, lm.y * h]

    def _calculate_ear(self, landmarks, eye_indices, w, h):
        """
        eye aspect ratio - drops to ~0 when the eye closes.
        used to detect blinks. formula: (v1 + v2) / (2 * h)
        """

        def get_point(idx):
            lm = landmarks.landmark[idx]
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

        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
