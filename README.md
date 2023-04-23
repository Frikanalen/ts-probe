# MPEG-2 Transport Stream Analyzer

This Python script analyzes an MPEG-2 transport stream with HE-AAC audio and H.264 video, decoding it into a circular buffer of raw audio and video. It exposes the following metrics as Prometheus metrics:

- Average video brightness
- Average audio amplitude (measured in both LUFS and dBFS)
- Transport stream packet rate
- Decode error rate
- Amount of motion in the video buffer
- Bitrate of the transport stream including padding packets
- Bitrate of the transport stream excluding padding packets

## Requirements

The script relies on the following Python libraries:

- requests
- pyav
- numpy
- prometheus_client

You can install these libraries using the following command:

```bash
pip install -r requirements.txt
```

## Usage

1. Set the environment variable `VIDEO_URL` to the HTTP URL of the live MPEG-2 transport stream.

```bash
export VIDEO_URL="http://example.com/path/to/your/mpeg2-ts-stream"
```

2. Run the script using Python:

```bash
python mpeg2_ts_analyzer.py
```

3. The script will start a Prometheus HTTP server on port 8000, which will expose the metrics. You can access the metrics at `http://localhost:8000/metrics`.

## Metrics

The script exposes the following metrics:

- `average_video_brightness`: Average video brightness (float)
- `average_audio_amplitude_lufs`: Average audio amplitude in LUFS (float)
- `average_audio_amplitude_dbfs`: Average audio amplitude in dBFS (float)
- `transport_stream_packet_rate`: Transport stream packet rate (float)
- `decode_error_rate`: Decode error rate (float)
- `motion`: Amount of motion in the video buffer, normalized between 0 and 1 (float)
- `bitrate_with_padding`: Bitrate of the transport stream including padding packets (float)
- `bitrate_without_padding`: Bitrate of the transport stream excluding padding packets (float)

The metrics are updated in real-time as the script processes the transport stream.

## Notes

This script is provided as a starting point and can be improved and optimized depending on your specific requirements.
