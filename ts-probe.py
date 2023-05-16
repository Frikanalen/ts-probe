import os
import time
import requests
import av
import numpy as np
from prometheus_client import start_http_server, Gauge
from pyloudnorm import Meter
from collections import deque
from io import BytesIO

# Initialize Prometheus metrics
video_brightness_gauge = Gauge('video_brightness', 'Average video brightness')
audio_amplitude_lufs_gauge = Gauge('audio_amplitude_lufs', 'Average audio amplitude in LUFS')
audio_amplitude_dbfs_gauge = Gauge('audio_amplitude_dbfs', 'Average audio amplitude in dBFS')
packet_rate_gauge = Gauge('ts_packet_rate', 'Transport stream packet rate')
decode_error_rate_gauge = Gauge('decode_error_rate', 'Decode error rate')
motion_gauge = Gauge('video_motion', 'Amount of motion in the video buffer')
bitrate_with_padding_gauge = Gauge('bitrate_with_padding', 'Bitrate of the transport stream including padding packets')
bitrate_without_padding_gauge = Gauge('bitrate_without_padding', 'Bitrate of the transport stream excluding padding packets')

# MPEG-2 transport stream URL
url = os.environ['VIDEO_URL']

sample_rate = 48000

meter = Meter(sample_rate)

# Parameters for circular buffer
buffer_size = 100
video_brightness_buffer = deque(maxlen=buffer_size)
audio_amplitude_buffer = deque(maxlen=buffer_size)
motion_buffer = deque(maxlen=buffer_size)

def get_ts_pid(packet_data):
    # Transport Stream packet header is 4 bytes long
    # The PID is stored in the 2nd and 3rd bytes
    pid = ((packet_data[1] & 0x1F) << 8) | packet_data[2]
    return pid


def get_dtype_and_scale_factor(sample_format):
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

def samples_to_numpy(audio_frame, dtype, scale_factor):
    audio_samples = [np.frombuffer(plane, dtype) for plane in audio_frame.planes]
    audio_samples = np.column_stack(audio_samples)
    if scale_factor != 1.0:
        audio_samples = audio_samples.astype(np.float32) / scale_factor
    return audio_samples

def calculate_lufs_and_dbfs(audio_frame):
    dtype, scale_factor = get_dtype_and_scale_factor(audio_frame.format.name)
    audio_samples = samples_to_numpy(audio_frame, dtype, scale_factor)

    # Print the number of channels in the audio frame
    num_channels = len(audio_frame.planes)

    # Calculate LUFS
    meter = Meter(audio_frame.rate, block_size=0.020)
    lufs = meter.integrated_loudness(audio_samples)

    # Calculate RMS in dBFS
    rms_value = np.sqrt(np.mean(np.square(audio_samples)))
    rms_dbfs = 20 * np.log10(rms_value)

    return lufs, rms_dbfs

# Function to calculate average video brightness
def calculate_average_brightness(frame):
    yuv_frame = frame.reformat(format='yuv420p')
    return np.mean(yuv_frame.planes[0])

# Function to calculate motion between two frames
def calculate_motion(frame1, frame2):
    gray_frame1 = frame1.reformat(format='gray8')
    gray_frame2 = frame2.reformat(format='gray8')
    abs_diff = np.abs(gray_frame1.to_ndarray().astype(int) - gray_frame2.to_ndarray().astype(int))
    mad = np.mean(abs_diff)
    normalized_mad = mad / 255
    return normalized_mad

# Custom file-like object that wraps a requests.Response object
class HTTPStream:
    packets_received = 0
    def __init__(self, response):
        self.response = response

    def read(self, size):
        self.packets_received += 1
        return self.response.raw.read(size)

    def close(self):
        self.response.close()

# Start Prometheus HTTP server
start_http_server(8000)

# Retrieve MPEG-2 transport stream and decode
response = requests.get(url, stream=True)
response.raw.decode_content = True
http_stream = HTTPStream(response)

stream = av.open(http_stream, mode='r')

packet_count = 0
padding_packet_count = 0
error_count = 0
decode_errors = []
prev_frame = None
start_time = time.time()
total_bytes_received = 0

for packet in stream.demux():
    packet_count += 1
    total_bytes_received += packet.size
    pid = get_ts_pid(bytes(packet))

    if pid == 0x1FFF:
        padding_packet_count += 1

    try:
        for frame in packet.decode():
            if isinstance(frame, av.video.frame.VideoFrame):
                avg_brightness = calculate_average_brightness(frame)
                video_brightness_buffer.append(avg_brightness)

                if prev_frame is not None:
                    motion = calculate_motion(prev_frame, frame)
                    motion_buffer.append(motion)
                prev_frame = frame

            elif isinstance(frame, av.audio.frame.AudioFrame):
                lufs, dbfs = calculate_lufs_and_dbfs(frame)
                audio_amplitude_buffer.append((lufs, dbfs))

    except av.AVError as e:
        error_count += 1
        decode_errors.append(e)

    elapsed_time = time.time() - start_time
    bitrate_with_padding = (total_bytes_received * 8) / elapsed_time
    bitrate_without_padding = ((total_bytes_received - padding_packet_count * 188) * 8) / elapsed_time

    # Update metrics
    video_brightness_gauge.set(np.mean(video_brightness_buffer))
    audio_amplitude_lufs_gauge.set(np.mean([amplitude[0] for amplitude in audio_amplitude_buffer]))
    audio_amplitude_dbfs_gauge.set(np.mean([amplitude[1] for amplitude in audio_amplitude_buffer]))
    packet_rate_gauge.set(packet_count / elapsed_time)
    decode_error_rate_gauge.set(error_count / packet_count)
    motion_gauge.set(np.mean(motion_buffer))
    bitrate_with_padding_gauge.set(bitrate_with_padding)
    bitrate_without_padding_gauge.set(bitrate_without_padding)

