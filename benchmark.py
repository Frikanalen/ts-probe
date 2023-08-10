import time
from dataclasses import dataclass
from typing import List

@dataclass
class DurationSample:
    begin : float
    end : float

    def trace(self, key):
        return '{"name":"%s","ph":"X","ts":%f,"dur":%f,"tid":1,"pid":1}\n' % (key, self.begin * 1000 * 1000, (self.end-self.begin) * 1000 * 1000)

class DurationSeries:
    def __init__(self, key:str, time_beginning:float):
        self.key:str = key
        self.time_beginning = time_beginning
        self.samples:List(DurationSample) = []
        self.sample_capacitiy:int = 0
        self.sample_count:int = 0
        self.sampling:bool = False

    def add_capacity(self):
        for n in range(100):
            self.samples.append(DurationSample(0, 0))
        self.sample_capacitiy += 100

    def begin(self):
        if (self.sample_count >= self.sample_capacitiy):
            self.add_capacity()
        self.samples[self.sample_count].begin = time.time() - self.time_beginning
        self.sampling = True

    def end(self):
        assert self.sampling
        self.samples[self.sample_count].end = time.time() - self.time_beginning
        self.sample_count += 1
        self.sampling = False

@dataclass
class MetricSample:
    time : float
    value : float
    id : str

    def trace(self, key):
        return '{"name":"%s","ts":%f,"ph":"C","pid":1,"args": {"%s":%f}}\n' % (key, self.time * 1000 * 1000, self.id, self.value)

class MetricSeries:
    def __init__(self, key:str, time_beginning:float):
        self.key:str = key
        self.time_beginning = time_beginning
        self.samples:List(MetricSample) = []
        self.sample_capacitiy:int = 0
        self.sample_count:int = 0

    def add_capacity(self):
        for n in range(100):
            self.samples.append(MetricSample(0, 0, ""))
        self.sample_capacitiy += 100

    def add(self, _id:str, value:float|int):
        if (self.sample_count >= self.sample_capacitiy):
            self.add_capacity()
        self.samples[self.sample_count].time = time.time() - self.time_beginning
        self.samples[self.sample_count].value = value
        self.samples[self.sample_count].id = _id
        self.sample_count += 1

@dataclass
class DummySample:
    def end(self):
        pass

class Benchmarker:
    "Simple benchmarker that generates a trace json file"
    def __init__(self, run:bool):
        "Run: Whether to generate a trace or not"
        self.run = run
        self.time_beginning = time.time()
        self.timings = {}
        self.metrics = {}

    def sample_begin(self, key:str):
        if not self.run:
            return DummySample()
        sampler = self.timings.setdefault(key, DurationSeries(key, self.time_beginning))
        sampler.begin()
        return sampler

    def sample_end(self, key:str):
        if not self.run:
            return
        assert key in self.timings
        sampler = self.timings[key]
        sampler.end(key)

    def add_metric_sample(self, key:str, value_id:str, value:float|int):
        if not self.run:
            return DummySample()
        sampler = self.metrics.setdefault(key, MetricSeries(key, self.time_beginning))
        sampler.add(value_id, value)
        return sampler

    def report(self, stem:str):
        # Chrome trace format
        # https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview
        if not self.run:
            return
        fn = f"{stem}.json"
        with open(fn, "w") as f:
            # Manually write out as JSON, as we want it fairly compact
            f.write("{\n")
            f.write('  "displayTimeUnit": "ms",\n')
            f.write('  "traceEvents": [\n')
            for key, series in self.timings.items():
                for n in range(series.sample_count):
                    sample = series.samples[n]
                    f.write(sample.trace(key))
            for key, series in self.metrics.items():
                for n in range(series.sample_count):
                    sample = series.samples[n]
                    f.write(sample.trace(key))
            f.write("]\n")
            f.write("}\n")
        pass
