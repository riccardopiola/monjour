import random as random_module
from typing import Protocol

class Distribution(Protocol):
    def __call__(self) -> float:
        ...

class constant(Distribution):
    value: float

    def __init__(self, value: float|int):
        self.value = round(float(value), 2)

    def __call__(self) -> float:
        return self.value

class uniform(Distribution):
    low: float
    high: float

    def __init__(self, low: float|int, high: float|int):
        self.low = float(low)
        self.high = float(high)

    def __call__(self) -> float:
        return round(random_module.uniform(self.low, self.high), 2)

class normal(Distribution):
    mean: float
    stdev: float

    def __init__(self, mean: float, stdev: float):
        self.mean = mean
        self.stdev = stdev

    def __call__(self) -> float:
        return round(random_module.normalvariate(self.mean, self.stdev), 2)