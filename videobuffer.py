""" Video analysis """
import logging
from collections import deque
import numpy as np
from av import VideoFrame

log = logging.getLogger(__name__)


def _calculate_motion(buffer: deque[VideoFrame]):
    """ Returns the average motion between the given frames. """
    if len(buffer) < 2:
        log.warning("Buffer too small to calculate motion")
        return 0

    prev_frame = buffer[0]
    abs_diff = 0

    for frame in buffer:
        abs_diff += np.abs(prev_frame.to_ndarray().astype(
            int) - frame.to_ndarray().astype(int))

        prev_frame = frame

    return np.mean(abs_diff/len(buffer)) / 255


# Function to calculate average video brightness


def calculate_average_brightness(buffer: deque[VideoFrame]):
    """ Returns the average brightness of the given frames. """

    # Return 0 and log a warning if the deque is empty
    if len(buffer) == 0:
        log.warning("Buffer empty, returning 0")
        return 0

    return np.mean([frame.planes[0] for frame in buffer])


BUFFER_SIZE = 10
FRAME_RATE = 50


class VideoBuffer():
    """ A circular buffer for video frames. 
    Contains analysis functions. """
    video_buffer = deque(maxlen=BUFFER_SIZE * FRAME_RATE)

    def append(self, frame: VideoFrame):
        """ Appends a frame to the buffer. """
        self.video_buffer.append(frame.reformat(format='gray8'))

    @property
    def avg_brightness(self):
        """ Returns the average brightness of the frames in the buffer. """
        return calculate_average_brightness(self.video_buffer)

    @property
    def motion(self):
        """ Returns the average motion between the frames in the buffer. """
        return _calculate_motion(self.video_buffer)
