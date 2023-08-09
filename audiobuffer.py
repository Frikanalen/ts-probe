""" AudioBuffer class for storing and analyzing audio samples. """""
from collections import deque
import numpy as np
from pyloudnorm import Meter
from av import AudioFrame
from logger import log

BUFFER_LENGTH_SECONDS = 1
SAMPLE_RATE = 48000
BUFFER_SIZE = BUFFER_LENGTH_SECONDS * SAMPLE_RATE


def _rms(buffer):
    return 20 * np.log10(np.sqrt(np.mean(np.square(buffer))))


def _samples_to_numpy(frame: AudioFrame, channel: int):
    dtype, scale_factor = _get_dtype_and_scale_factor(frame.format.name)
    audio_samples = np.frombuffer(frame.planes[channel], dtype)
    if scale_factor != 1.0:
        audio_samples = audio_samples.astype(np.float32) / scale_factor
    return audio_samples


def _get_dtype_and_scale_factor(sample_format):
    if sample_format == 's16':
        dtype = np.int16
        scale_factor = np.iinfo(dtype).max
    elif sample_format == 's32':
        dtype = np.int32
        scale_factor = np.iinfo(dtype).max
    elif sample_format == 'fltp':
        dtype = np.float32
        scale_factor = 1.0
    elif sample_format == 'dbl':
        dtype = np.float64
        scale_factor = 1.0
    else:
        raise ValueError(f"Unsupported sample format: {sample_format}")
    return dtype, scale_factor


class AudioBuffer():
    """ A circular buffer for audio samples. Includes LUFS and dBFS analysis. """
    left_buffer = deque(maxlen=BUFFER_SIZE)
    right_buffer = deque(maxlen=BUFFER_SIZE)
    meter = Meter(SAMPLE_RATE)

    def append(self, frame: AudioFrame):
        """ Appends a frame to the buffer."""
        # Only stereo supported for now
        assert len(frame.planes) == 2

        self.left_buffer.extend(_samples_to_numpy(frame, 0))
        self.right_buffer.extend(_samples_to_numpy(frame, 1))

    def lufs(self):
        """ Returns the LUFS value for the given channel. """

        if (len(self.left_buffer) < BUFFER_SIZE or len(self.right_buffer) < BUFFER_SIZE):
            log.info(
                f"Buffer {len(self.left_buffer)} too small to calculate LUFS")
            return 0

        log.debug("Calculating LUFS")
        left_array = np.array(self.left_buffer)
        right_array = np.array(self.right_buffer)
        return self.meter.integrated_loudness(np.array([left_array, right_array]).T)

    def dbfs(self, channel):
        """ Returns the RMS value in dBFS for the given channel. """
        if channel == 0:
            return _rms(self.left_buffer)
        if channel == 1:
            return _rms(self.right_buffer)

        raise ValueError(f"Unsupported channel: {channel}")
