""" Transport stream probe utility """
import os
import time
import av
from av import VideoFrame, AudioFrame
from audiobuffer import AudioBuffer
from videobuffer import VideoBuffer
from prometheus import Prometheus
from logger import log
from benchmark import Benchmarker


DEFAULT_VIDEO_URL = 'http://simula.frikanalen.no:9094/frikanalen.ts'
PROMETHEUS_PORT = 8000
# Generates a trace-ts-probe.json that can be opened in about:tracing or https://ui.perfetto.dev/
BENCHMARK = False
# Use threading.
DO_THREADING = False
# Interval between analysis
VIDEO_PROBE_INTERVAL = 5
AUDIO_PROBE_INTERVAL = 5

# Benchmark tuning
BENCHMARK_STOP_FRAME = -1
if BENCHMARK:
    BENCHMARK_STOP_FRAME = 100
if BENCHMARK:
    VIDEO_PROBE_INTERVAL = 1
    AUDIO_PROBE_INTERVAL = 1

# MPEG-2 transport stream URL
url = os.environ.get('VIDEO_URL', None)
if url is None:
    url = DEFAULT_VIDEO_URL
    log.warning("No video URL specified, using default: %s" % url)

# Create buffers
audio_buffer = AudioBuffer()
video_buffer = VideoBuffer()


# Start Prometheus HTTP server
prom = Prometheus()
prom.listen(PROMETHEUS_PORT)


def run():
    bench = Benchmarker(BENCHMARK)
    smp = bench.sample_begin("Warmup")
    log.info("Opening stream: %s" % url)
    stream = av.open(url)
    if DO_THREADING:
        stream.streams.video[0].thread_type = "AUTO"
    log.info("Stream is open")
    smp.end()
    # Bookkeeping
    local_video_frame_count = 0 # Used by benchmark to track frame
    video_interval_counter = 0  # Used to track intervals
    audio_interval_counter = 0
    # Start the clock (for benchmarking)
    START_TIME = time.time()
    while True:
        frame_smp = bench.sample_begin("Frame")
        frame_decode_smp = bench.sample_begin("Frame-Decode")
        frame_iter = iter(stream.decode())
        try:
            frame = next(frame_iter)
            frame_decode_smp.end()
            if isinstance(frame, VideoFrame):
                prom.video_frame_count.inc()
                local_video_frame_count += 1

                video_interval_counter += 1
                if VIDEO_PROBE_INTERVAL == video_interval_counter:
                    #
                    video_analysis_smp = bench.sample_begin("Video-Analysis")
                    # Add frame
                    video_buffer.append(frame)
                    avg_brightness = video_buffer.avg_brightness
                    motion = video_buffer.motion
                    prom.video_brightness_gauge.set(avg_brightness)
                    prom.motion_gauge.set(motion)
                    video_interval_counter = 0
                    video_analysis_smp.end()
                    if BENCHMARK:
                        motion *= 1000
                        avg_brightness *= 1000
                        print(f"Motion: {motion:12.3f} Brightness: {avg_brightness:12.3f}")
                        bench.add_metric_sample("video", "motion", motion)
                        bench.add_metric_sample("video", "brightness", avg_brightness)

            elif isinstance(frame, AudioFrame):
                audio_buffer.append(frame)
                audio_interval_counter += 1
                if AUDIO_PROBE_INTERVAL == audio_interval_counter:
                    audio_analysis_smp = bench.sample_begin("Audio-Analysis")
                    lufs = audio_buffer.lufs()
                    dbfs = audio_buffer.dbfs(0)
                    prom.audio_amplitude_lufs_gauge.set(lufs)
                    prom.audio_amplitude_dbfs_gauge.set(dbfs)
                    audio_interval_counter = 0
                    audio_analysis_smp.end()
                    bench.add_metric_sample("audio", "lufs", lufs)
                    bench.add_metric_sample("audio", "dbfs", dbfs)

            if BENCHMARK:
                if local_video_frame_count == BENCHMARK_STOP_FRAME:
                    dt = time.time() - START_TIME
                    avg = dt / local_video_frame_count * 1000;
                    print(f"Average: {avg:.3}ms")
                    break
        except av.AVError as e:
            frame_decode_smp.end()
            log.error(e)
            prom.decode_error_count.inc()
            reopen_smp = bench.sample_begin("Re-open")
            stream = av.open(url)
            reopen_smp.end()

        except KeyboardInterrupt:
            log.info("Keyboard interrupt")
            break
        frame_smp.end()
    bench.report("trace-ts-probe")

run()
