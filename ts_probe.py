""" Transport stream probe utility """
import os
import time
from collections import deque
import av
from av import VideoFrame, AudioFrame
from audiobuffer import AudioBuffer
from videobuffer import VideoBuffer
from prometheus import Prometheus

prom = Prometheus()

# MPEG-2 transport stream URL
url = os.environ.get(
    'VIDEO_URL', 'http://simula.frikanalen.no:9094/frikanalen.ts')


# Parameters for circular buffer
BUFFER_SIZE = 100
video_brightness_buffer = deque(maxlen=BUFFER_SIZE)
audio_amplitude_buffer = deque(maxlen=BUFFER_SIZE)
motion_buffer = deque(maxlen=BUFFER_SIZE)


# Start Prometheus HTTP server
prom.listen(8000)

stream = av.open(url)

padding_packet_count: int = 0
START_TIME = time.time()
total_bytes_received: int = 0

audio_buffer = AudioBuffer()
video_buffer = VideoBuffer()

while True:
    try:
        for frame in stream.decode():
            print("frame")

            if isinstance(frame, VideoFrame):
                print("video frame")
                prom.video_frame_count.inc()
                video_buffer.append(frame)
                prom.video_brightness_gauge.set(video_buffer.avg_brightness)
                prom.motion_gauge.set(video_buffer.motion)

            elif isinstance(frame, AudioFrame):
                print("audio frame")
                audio_buffer.append(frame)
                prom.audio_amplitude_lufs_gauge.set(audio_buffer.lufs())
                prom.audio_amplitude_dbfs_gauge.set(audio_buffer.dbfs(0))

    except av.AVError as e:
        print(e)
        prom.decode_error_count.inc()
        stream = av.open(url)
