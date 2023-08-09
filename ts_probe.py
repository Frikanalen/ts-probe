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
BUFFER_SIZE = 100

# MPEG-2 transport stream URL
url = os.environ.get('VIDEO_URL', None)

if url is None:
    url = DEFAULT_VIDEO_URL
    log.warning("No video URL specified, using default: %s" % url)

audio_buffer = AudioBuffer()
video_buffer = VideoBuffer()
padding_packet_count: int = 0
total_bytes_received: int = 0
START_TIME = time.time()

# Start Prometheus HTTP server
prom.listen(PROMETHEUS_PORT)

log.info("Opening stream: %s" % url)
stream = av.open(url)

while True:
    log.info("Stream is open")
    try:
        for frame in stream.decode():
            if isinstance(frame, VideoFrame):
                prom.video_frame_count.inc()
                video_buffer.append(frame)
                prom.video_brightness_gauge.set(video_buffer.avg_brightness)
                prom.motion_gauge.set(video_buffer.motion)

            elif isinstance(frame, AudioFrame):
                audio_buffer.append(frame)
                prom.audio_amplitude_lufs_gauge.set(audio_buffer.lufs())
                prom.audio_amplitude_dbfs_gauge.set(audio_buffer.dbfs(0))

    except av.AVError as e:
        log.error(e)
        prom.decode_error_count.inc()
        stream = av.open(url)

    except KeyboardInterrupt:
        log.info("Keyboard interrupt")
        break

    except Exception as e:
        log.error(e)
        break
