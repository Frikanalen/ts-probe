""" Video analysis """
from logger import log
from collections import deque
import numpy as np
import numpy.typing as npt
from av import VideoFrame
from itertools import islice

BUFFER_SIZE = 25
REDUCE_BEFORE_MOTION = True
BLUR_BEFORE_MOTION = False
BLUR_KERNEL = np.array([0.20, 0.20, 0.20, 0.20, 0.20])

class ProbeFrame:
    " A frame including metrics of the videoframe"
    def __init__(self, frame: VideoFrame, last_frame: "ProbeFrame"):
        self.frame:npt.NDArray[np.fl] = frame.reformat(format='gray8').to_ndarray().astype(np.uint8)
        # Calculate brightness
        self.brightness = np.mean(self.frame)
        # Resize
        if REDUCE_BEFORE_MOTION:
            # Non-interpolating reduction. This is to reduce the chance of triggering on interlaced stalls
            # If one wants to reduce further, I recommend proper resampling
            self.frame = self.frame[::2, ::2].astype("float32") / 255
        # Box-blur
        if BLUR_BEFORE_MOTION:
            self.frame = np.apply_along_axis(lambda x: np.convolve(x, BLUR_KERNEL, mode='same'), 0, self.frame)
            self.frame = np.apply_along_axis(lambda x: np.convolve(x, BLUR_KERNEL, mode='same'), 1, self.frame)
        # Calculate motion
        if last_frame:
            self.motion = np.mean(np.power(np.abs(self.frame - last_frame.frame), 0.5))
        self.has_motion:bool = last_frame is not None

class VideoBuffer():
    """ A circular buffer for video frames.
    Contains analysis functions. """
    video_buffer = deque(maxlen=BUFFER_SIZE)
    last_frame = None

    def append(self, frame: VideoFrame):
        """ Appends a frame to the buffer. """
        pb = ProbeFrame(frame, self.last_frame)
        self.video_buffer.append(pb)
        self.last_frame = pb

    @property
    def avg_brightness(self):
        """ Returns the average brightness of the frames in the buffer. """
        #return _avg_brightness(self.video_buffer)
        l = [f.brightness for f in self.video_buffer]
        nda = np.array(l, dtype="float")
        return np.mean(nda) / 255

    @property
    def motion(self):
        """ Returns the average motion between the frames in the buffer. """
        #return _motion(self.video_buffer)
        l = [f.motion for f in self.video_buffer if f.has_motion]
        nda = np.array(l, dtype="float")
        return np.mean(nda)

