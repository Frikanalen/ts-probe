""" Prometheus metrics. """
from prometheus_client import Gauge, Counter, start_http_server


class Prometheus():
    """ Prometheus metrics. """
    video_brightness_gauge = Gauge(
        'tsprobe_video_brightness', 'Average video brightness')
    audio_amplitude_lufs_gauge = Gauge(
        'tsprobe_audio_amplitude_lufs', 'Average audio amplitude in LUFS')
    audio_amplitude_dbfs_gauge = Gauge(
        'tsprobe_audio_amplitude_dbfs', 'Average audio amplitude in dBFS')
    decode_error_count = Counter(
        'tsprobe_decode_errors_total', 'Total number of decode errors')
    video_frame_count = Counter(
        'tsprobe_frames_total', 'Total number of video frames received')
    motion_gauge = Gauge(
        'tsprobe_video_motion', 'Amount of motion in the video buffer')

    def listen(self, port):
        """ Starts the Prometheus HTTP server. """
        start_http_server(port)
