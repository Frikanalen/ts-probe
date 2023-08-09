import numpy as np
from pyloudnorm import Meter
from av import AudioFrame
from logger import log

BUFFER_LENGTH_SECONDS = 1
SAMPLE_RATE = 48000
NUM_CHANNELS = 2
BUFFER_SIZE = BUFFER_LENGTH_SECONDS * SAMPLE_RATE

SAMPLE_FORMATS = {
    's16': (np.int16, np.iinfo(np.int16).max),
    's32': (np.int32, np.iinfo(np.int32).max),
    'fltp': (np.float32, 1.0),
    'dbl': (np.float64, 1.0)
}


def _rms(buffer):
    return 20 * np.log10(np.sqrt(np.mean(np.square(buffer))))


def _samples_to_numpy(frame: AudioFrame, channel: int):
    dtype, scale_factor = SAMPLE_FORMATS.get(frame.format.name, (None, None))
    if dtype is None:
        raise ValueError(f"Unsupported sample format: {frame.format.name}")
    audio_samples = np.frombuffer(frame.planes[channel], dtype)
    if scale_factor != 1.0:
        audio_samples = audio_samples.astype(np.float32) / scale_factor
    return audio_samples


class AudioBuffer():
    """ A circular buffer for audio samples. Includes LUFS and dBFS analysis. """

    def __init__(self):
        self.buffer = np.zeros((NUM_CHANNELS, BUFFER_SIZE), dtype=np.float32)
        self.meter = Meter(SAMPLE_RATE)

    def append(self, frame: AudioFrame):
        """ Appends a frame to the buffer."""
        assert len(frame.planes) == 2

        num_samples = frame.samples

        self.buffer[0] = np.roll(self.buffer[0], shift=-num_samples)
        self.buffer[0][-num_samples:] = _samples_to_numpy(frame, 0)
        self.buffer[1] = np.roll(self.buffer[1], shift=-num_samples)
        self.buffer[1][-num_samples:] = _samples_to_numpy(frame, 1)

    def lufs(self):
        """ Returns the LUFS value for the given channel. """
        log.debug("Calculating LUFS")
        return self.meter.integrated_loudness(self.buffer.T)

    def dbfs(self, channel):
        """ Returns the RMS value in dBFS for the given channel. """
        if channel == 0:
            return _rms(self.buffer[0])
        if channel == 1:
            return _rms(self.buffer[1])
        raise ValueError(f"Unsupported channel: {channel}")
