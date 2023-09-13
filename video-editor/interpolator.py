import math
import os
from multiprocessing import Event
from threading import Lock, Thread
from typing import Any

import cv2
import numpy as np


class FrameBuffer:
    """
    Stores frames in a ringbuffer.
    Provides methods for accessing and pushing frames.
    Double pointer method: put index and get index.
    """

    def __init__(self, sample_rate: int):
        self.buffer = [
            (np.array([], dtype=np.uint8), np.array([], dtype=np.uint8))
            for _ in range(sample_rate)
        ]
        self.buffer_len = sample_rate
        self.buffer_put_idx = 0
        self.buffer_get_idx = -1

    def _increment_put_idx(self) -> None:
        """
        Moves the put index forward without changing the buffer.
        """
        self.buffer_put_idx = (self.buffer_put_idx + 1) % self.buffer_len

    def _increment_get_idx(self) -> None:
        """
        Moves the get index forward without changing the buffer.
        """
        self.buffer_get_idx = (self.buffer_get_idx + 1) % self.buffer_len

    def put(self, frame: np.ndarray, gray: np.ndarray) -> None:
        """
        Pushes a frame and its grayscale version into the buffer.
        Then moves the put index forward.
        """
        self.buffer[self.buffer_put_idx] = (frame, gray)
        self._increment_put_idx()

    def get(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns the content of the buffer at the current get index.
        Then moves the get index forward.
        """
        frame, gray = self.buffer[self.buffer_get_idx]
        self._increment_get_idx()
        return frame, gray

    def lookup_last(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns the content of the buffer at the previous put index.
        """
        return self.buffer[self.buffer_put_idx - 1]


class Interpolator(Thread):
    """
    Consumes keyframes with polygons and skipframes.
    Interpolates polygon positions for skipframes.
    Sends all frames to a writer in the order they were received.
    """

    OPTICAL_FLOW_WINDOW = (31, 31)
    OPTICAL_FLOW_DIST = np.linalg.norm(np.array(OPTICAL_FLOW_WINDOW))
    GRAY_PADDING = OPTICAL_FLOW_WINDOW[0]
    PADDING_PARAMS = (
        GRAY_PADDING,
        GRAY_PADDING,
        GRAY_PADDING,
        GRAY_PADDING,
        cv2.BORDER_REPLICATE,
        None,
        0,
    )

    def __init__(self, sample_rate: int, writer: Any):
        super().__init__()
        self.writer = writer
        self.frame_buffer = FrameBuffer(2 * sample_rate)

        # State variables
        self.cur_frame: np.ndarray = np.ndarray([], dtype=np.uint8)
        self.cur_gray: np.ndarray = np.ndarray([], dtype=np.uint8)
        self.cur_keyframe_num = 0
        self.prev_keyframe_num = 0
        self.cur_polygons: list[np.ndarray] = []
        self.old_polygons: list[np.ndarray] = []

        # Synchonization variables
        self.keyframe_event = Event()
        self.processing_lock = Lock()
        self.quit = False

        # Read blur parameters form environment
        try:
            video_blur_str = os.environ.get("VIDEO_BLUR")
            if video_blur_str:
                self.blur_amount = int(video_blur_str)
                self.blur_amount = max(1, min(10, self.blur_amount))
        except Exception:
            self.blur_amount = 3

    def run(self) -> None:
        """
        Checks whether the new keyframe has arrived in a loop.
        If so, sets a lock and starts processing it.
        """
        while not self.quit:
            self.keyframe_event.wait()
            self.keyframe_event.clear()
            if self.cur_keyframe_num > self.prev_keyframe_num:
                with self.processing_lock:
                    self._process_keyframe()

    def _bounding_box(self, polygon: np.ndarray, shape: tuple[int, ...]) -> list[int]:
        """
        Returns the bounding box of a polygon.
        Right and bottom edges are exclusive.
        Trims the box to fit the frame.
        """
        box = [
            math.floor(np.min(polygon[:, 0])),
            math.floor(np.min(polygon[:, 1])),
            math.ceil(np.max(polygon[:, 0])) + 1,
            math.ceil(np.max(polygon[:, 1])) + 1,
        ]
        box[0] = max(0, box[0])
        box[1] = max(0, box[1])
        box[2] = min(shape[1], box[2])
        box[3] = min(shape[0], box[3])

        return box

    def _blur_polygons(self, frame: np.ndarray, polygons: list[np.ndarray]):
        """
        Draws blurred polygons to the frame.
        """
        result = frame.copy()
        channel_count = frame.shape[2]
        ignore_mask_color = (255,) * channel_count

        for poly in polygons:
            box = self._bounding_box(poly, frame.shape)
            polygon_height = box[3] - box[1]
            polygon_width = box[2] - box[0]
            if polygon_height < 1 or polygon_width < 1:
                continue

            # Prep mask
            window = result[box[1] : box[3], box[0] : box[2]]
            mask = np.zeros(window.shape, dtype=np.uint8)
            cv2.fillConvexPoly(
                mask, np.int32(poly - box[:2]), ignore_mask_color, cv2.LINE_AA
            )

            # Prep totally blurred image
            kernel_width = (polygon_width // self.blur_amount) | 1
            kernel_height = (polygon_height // self.blur_amount) | 1
            blurred_window = cv2.GaussianBlur(window, (kernel_width, kernel_height), 0)

            # Combine original and blur
            result[box[1] : box[3], box[0] : box[2]] = cv2.bitwise_and(
                window, cv2.bitwise_not(mask)
            ) + cv2.bitwise_and(blurred_window, mask)

        self.writer.write(result)

    def _is_consistent(self, shift: np.ndarray) -> bool:
        """
        Checks if the optical flow shifts are consistent between each other.
        """
        lengths = np.linalg.norm(shift, axis=1)
        if np.max(lengths) < 2:
            return True

        # Check average displacement length
        avg_shift = np.mean(shift, axis=0)
        avg_shift_len = np.linalg.norm(avg_shift)
        if avg_shift_len < 0.5:
            return False
        avg_shift /= avg_shift_len  # normalize

        # Check if direction is consistent with the average
        for i, vec in enumerate(shift):
            # This will not work if the polygon is moving towards the camera
            # TODO: come up with a better check
            if np.dot(vec, avg_shift) < 0.5 * lengths[i]:
                return False

        return True

    def _interpolate_polygons(
        self,
    ) -> list[tuple[np.ndarray, np.ndarray, list[np.ndarray]]]:
        """
        Approximates blurred polygons between keyframes.
        Returns a List of frames to write and their approximated polygons.
        """
        # Propagate old polygons forward with optical flow
        num_frames = self.cur_keyframe_num - self.prev_keyframe_num - 1
        frames_to_blur = []
        _, prev_gray = self.frame_buffer.get()
        prev_polygons = self.old_polygons
        for _ in range(num_frames):
            next_frame, next_gray = self.frame_buffer.get()
            polygons = []
            for poly in prev_polygons:
                new_poly, _, _ = cv2.calcOpticalFlowPyrLK(
                    prev_gray,
                    next_gray,
                    poly + self.GRAY_PADDING,
                    None,
                    winSize=self.OPTICAL_FLOW_WINDOW,
                    maxLevel=10,
                    criteria=(
                        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                        10,
                        0.03,
                    ),
                )
                new_poly = new_poly - self.GRAY_PADDING
                shift = new_poly - poly
                if self._is_consistent(shift):
                    polygons.append(new_poly)
            frames_to_blur.append((next_frame, next_gray, polygons))
            prev_gray = next_gray
            prev_polygons = polygons

        # Propagate new polygons backward with optical flow
        next_polygons = self.cur_polygons
        next_gray = self.cur_gray
        for i in range(num_frames):
            _, prev_gray, inter_polygons = frames_to_blur[-i - 1]
            polygons = []
            for poly in next_polygons:
                new_poly, _, _ = cv2.calcOpticalFlowPyrLK(
                    next_gray,
                    prev_gray,
                    poly + self.GRAY_PADDING,
                    None,
                    winSize=self.OPTICAL_FLOW_WINDOW,
                    maxLevel=10,
                    criteria=(
                        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                        10,
                        0.03,
                    ),
                )
                new_poly -= self.GRAY_PADDING
                shift = new_poly - poly
                if self._is_consistent(shift):
                    polygons.append(new_poly)
            inter_polygons.extend(polygons)
            next_gray = prev_gray
            next_polygons = polygons

        return frames_to_blur

    def _process_keyframe(self) -> None:
        """
        Uses new keyframe to interpolates the previous sequence of skipframes.
        Sends all frames and their polygons to the writer.
        """
        # Draw skipframes
        frames_to_blur = self._interpolate_polygons()
        for skipframe, _, polygons in frames_to_blur:
            self._blur_polygons(skipframe, polygons)
        # Draw current frame
        self._blur_polygons(self.cur_frame, self.cur_polygons)

        # Update state variables
        self.old_polygons = self.cur_polygons
        self.prev_keyframe_num = self.cur_keyframe_num

    def _gray_pad(self, frame: np.ndarray) -> np.ndarray:
        """
        Converts a frame to grayscale and pads it.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.copyMakeBorder(gray, *self.PADDING_PARAMS)

    def feed_keyframe(
        self, frame: np.ndarray, frame_count: int, polygons: list[np.ndarray]
    ) -> None:
        """
        Waits if the previous keyframe is still being processed.
        Otherwise records the new keyframe and its info.
        Then triggers the processing event and returns.
        """
        with self.processing_lock:
            gray = self._gray_pad(frame)
            self.frame_buffer.put(frame, gray)

            # Update state variables
            self.cur_frame = frame
            self.cur_gray = gray
            self.cur_keyframe_num = frame_count
            self.cur_polygons = polygons

        self.keyframe_event.set()  # signal to start processing

    def feed_skipframe(self, frame: np.ndarray) -> None:
        """
        Stacks skipframes into a buffer.
        """
        self.frame_buffer.put(frame, self._gray_pad(frame))

    def is_flush_needed(self, frame_count: int) -> bool:
        """
        Determines if the buffer has remaining skipframes to be flushed.
        """
        return self.cur_keyframe_num < frame_count

    def flush(self, frame_count: int, polygons: list[np.ndarray]) -> None:
        """
        Extracts the previously pushed skipframe.
        Then processes it as a new keyframe.
        """
        with self.processing_lock:
            # Check if last frame is already processed
            if self.cur_keyframe_num >= frame_count:
                return

            # Update state variables
            self.cur_frame, self.cur_gray = self.frame_buffer.lookup_last()
            self.cur_keyframe_num = frame_count
            self.cur_polygons = polygons

        self.keyframe_event.set()  # signal to start processing

    def close(self) -> None:
        """
        Finishes processing frames and stops the thread.
        """
        with self.processing_lock:
            self.quit = True
            self.keyframe_event.set()
        self.join()
