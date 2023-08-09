""" Transport stream probe utility """
import os
import time
from collections import deque
import av
from av import VideoFrame, AudioFrame
from audiobuffer import AudioBuffer
from videobuffer import VideoBuffer
from prometheus import Prometheus
from logger import log

prom = Prometheus()
DEFAULT_VIDEO_URL = 'http://simula.frikanalen.no:9094/frikanalen.ts'
PROMETHEUS_PORT = 8000
# MPEG-2 transport stream URL
url = os.environ.get('VIDEO_URL', None)

if url is None:
    url = DEFAULT_VIDEO_URL
    log.warning("No video URL specified, using default: %s" % url)

audio_buffer = AudioBuffer()
video_buffer = VideoBuffer()
START_TIME = time.time()

# Start Prometheus HTTP server
prom.listen(PROMETHEUS_PORT)


def run():
    VIDEO_PROBE_INTERVAL = 10
    AUDIO_PROBE_INTERVAL = 10
    log.info("Opening stream: %s" % url)
    stream = av.open(url)
    while True:
        log.info("Stream is open")
        try:
            for frame in stream.decode():
                if isinstance(frame, VideoFrame):
                    prom.video_frame_count.inc()

                    VIDEO_PROBE_INTERVAL -= 1
                    if VIDEO_PROBE_INTERVAL == 0:
                        video_buffer.append(frame)
                        prom.video_brightness_gauge.set(
                            video_buffer.avg_brightness)
                        prom.motion_gauge.set(
                            video_buffer.motion)
                        VIDEO_PROBE_INTERVAL = 20

                elif isinstance(frame, AudioFrame):
                    audio_buffer.append(frame)
                    AUDIO_PROBE_INTERVAL -= 1

                    if AUDIO_PROBE_INTERVAL == 0:
                        prom.audio_amplitude_lufs_gauge.set(
                            audio_buffer.lufs())
                        prom.audio_amplitude_dbfs_gauge.set(
                            audio_buffer.dbfs(0))
                        AUDIO_PROBE_INTERVAL = 20

        except av.AVError as e:
            log.error(e)
            prom.decode_error_count.inc()
            stream = av.open(url)

        except KeyboardInterrupt:
            log.info("Keyboard interrupt")
            break


run()
