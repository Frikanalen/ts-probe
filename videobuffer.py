""" Video analysis """
from logger import log
import numpy as np
import numpy.typing as npt
from av import VideoFrame

BUFFER_SIZE = 10
FRAME_RATE = 50


def compute_frame_difference(frame1: npt.NDArray[np.uint8], frame2: npt.NDArray[np.uint8]) -> float:
    """Compute the difference between two frames."""
    diff = np.subtract(frame1, frame2, dtype=np.int16)
    return np.sum(np.abs(diff))


def compute_frame_brightness(frame: npt.NDArray[np.uint8]) -> float:
    """Compute the brightness of a frame."""
    return np.sum(frame)


class VideoBuffer():
    height = None
    width = None

    """ A buffer for video frames. Contains analysis functions. """

    def __init__(self):
        self.buffer_size = BUFFER_SIZE * FRAME_RATE
        self.video_buffer = np.empty(
            (self.buffer_size, 1, 1), dtype=np.uint8)
        self.index = 0
        self.total_brightness = 0.0
        self.total_motion = 0.0

    def _initialize_buffer(self, height, width):
        """ Reinitialize the video buffer with a new resolution. """
        self.video_buffer = np.empty(
            (self.buffer_size, height, width), dtype=np.uint8)
        self.index = 0
        self.height = height
        self.width = width
        log.info(
            "Initialized video buffer with resolution: {}x{}".format(height, width))

    def append(self, frame: VideoFrame):
        """ Appends a frame to the buffer. """
        new_frame = frame.reformat(format='gray8').to_ndarray()
        frame_height, frame_width = new_frame.shape

        # Check if the resolution of the incoming frame matches the buffer's resolution
        if frame_height != self.height or frame_width != self.width:
            self._initialize_buffer(frame_height, frame_width)

        # Adjust total brightness
        self.total_brightness -= compute_frame_brightness(
            self.video_buffer[self.index])
        self.total_brightness += compute_frame_brightness(new_frame)

        # Adjust total motion if there's a previous frame
        if self.index > 0:
            prev_index = self.index - 1
        else:
            prev_index = self.buffer_size - 1
        self.total_motion -= compute_frame_difference(
            self.video_buffer[prev_index], self.video_buffer[self.index])
        self.total_motion += compute_frame_difference(
            new_frame, self.video_buffer[prev_index])

        self.video_buffer[self.index] = new_frame
        self.index = (self.index + 1) % self.buffer_size

    @property
    def avg_brightness(self):
        return self.total_brightness / (self.buffer_size * self.height * self.width)

    @property
    def motion(self):
        return self.total_motion / (self.buffer_size * self.height * self.width)
