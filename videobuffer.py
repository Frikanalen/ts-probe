""" Video analysis """
from logger import log
from collections import deque
import numpy as np
import numpy.typing as npt
from av import VideoFrame
from itertools import islice

BUFFER_SIZE = 10
FRAME_RATE = 50


def _motion(buffer: deque[npt.NDArray[np.uint8]]):
    """ Returns the average motion between the given frames. """
    if len(buffer) < 2:
        log.warning("Buffer too small to calculate motion")
        return 0

    frame_diffs = [
        np.mean(abs(buffer[i].astype(np.int16) - frame).astype(np.uint8))
        for i, frame in enumerate(islice(buffer, 1, None))
    ]

    # Return the mean of the absolute differences
    return np.mean(frame_diffs) / 255


def _avg_brightness(buffer: deque[npt.NDArray[np.uint8]]):
    """ Returns the average brightness of the given frames. """

    if len(buffer) == 0:
        log.warning("Buffer empty, returning 0")
        return 0

    return np.mean(buffer) / 255


class VideoBuffer():
    """ A circular buffer for video frames. 
    Contains analysis functions. """
    video_buffer = deque(maxlen=BUFFER_SIZE * FRAME_RATE)

    def append(self, frame: VideoFrame):
        """ Appends a frame to the buffer. """
        self.video_buffer.append(frame.reformat(
            format='gray8').to_ndarray().astype(np.uint8))

    @property
    def avg_brightness(self):
        """ Returns the average brightness of the frames in the buffer. """
        return _avg_brightness(self.video_buffer)

    @property
    def motion(self):
        """ Returns the average motion between the frames in the buffer. """
        return _motion(self.video_buffer)
