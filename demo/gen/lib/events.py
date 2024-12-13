from enum import Enum
import random as random_module
from typing import Any, Iterable, Protocol

class Distribution(Protocol):
    def __call__(self) -> float: ...
    def __str__(self, value: float) -> "Distribution": ...

    # Arithmetic operations
    def __mul__(self, value: float) -> "Distribution": ...
    def __add__(self, value: float) -> "Distribution": ...
    def __truediv__(self, value: float) -> "Distribution": ...
    def __sub__(self, value: float) -> "Distribution": ...

class constant(Distribution):
    value: float

    def __init__(self, value: float|int):
        self.value = round(float(value), 2)

    def __call__(self) -> float:
        return self.value

    def __str__(self):
        return f'constant({self.value})'

    def __mul__(self, value: float) -> "constant":
        return constant(self.value * value)

    def __add__(self, value: float) -> "constant":
        return constant(self.value + value)

    def __truediv__(self, value: float) -> "constant":
        return constant(self.value / value)

    def __sub__(self, value: float) -> "constant":
        return constant(self.value - value)

class uniform(Distribution):
    low: float
    high: float

    def __init__(self, low: float|int, high: float|int):
        self.low = float(low)
        self.high = float(high)

    def __call__(self) -> float:
        return random_module.uniform(self.low, self.high)

    def __str__(self):
        return f'uniform({self.low}, {self.high})'

    def __mul__(self, value: float) -> "uniform":
        return uniform(self.low * value, self.high * value)

    def __add__(self, value: float) -> "uniform":
        return uniform(self.low + value, self.high + value)

    def __truediv__(self, value: float) -> "uniform":
        return uniform(self.low / value, self.high / value)

    def __sub__(self, value: float) -> "uniform":
        return uniform(self.low - value, self.high - value)

class normal(Distribution):
    mean: float
    stdev: float

    def __init__(self, mean: float, stdev: float|int):
        self.mean = float(mean)
        self.stdev = float(stdev)

    def __call__(self) -> float:
        return random_module.normalvariate(self.mean, self.stdev)

    def __str__(self):
        return f'normal({self.mean}, {self.stdev})'

    def __mul__(self, value: float) -> "normal":
        return normal(self.mean * value, self.stdev * value)

    def __add__(self, value: float) -> "normal":
        return normal(self.mean + value, self.stdev + value)

    def __truediv__(self, value: float) -> "normal":
        return normal(self.mean / value, self.stdev / value)

    def __sub__(self, value: float) -> "normal":
        return normal(self.mean - value, self.stdev - value)

class EventOccurrance(Enum):
    Daily = 1
    Weekly = 2
    Monthly = 3

class Event:
    # How often the probabiliy of occurrance for this event is calculated
    occurrance: EventOccurrance

    # Probability of this event occurring
    occurrance_prob: float

    # Amount distribution
    amount_dist: Distribution

    def __init__(self, amount: Distribution|float|int, occurrance: EventOccurrance|None = None, occurrance_prob: float|None = None,
                 daily: float|None = None, weekly: float|None = None, monthly: float|None = None):
        amt_dist = constant(amount) if isinstance(amount, float) or isinstance(amount, int) else amount
        self.amount_dist = amt_dist
        if occurrance is not None:
            self.occurrance = occurrance
            assert occurrance_prob is not None
            self.occurrance_prob = occurrance_prob
        elif daily is not None:
            self.occurrance = EventOccurrance.Daily
            self.occurrance_prob = daily
        elif weekly is not None:
            self.occurrance = EventOccurrance.Weekly
            self.occurrance_prob = weekly
        elif monthly is not None:
            self.occurrance = EventOccurrance.Monthly
            self.occurrance_prob = monthly
        else:
            raise ValueError('One of daily, weekly or monthly must be provided')

    def __add__(self, value: float) -> "Event":
        return Event(self.amount_dist + value, self.occurrance, self.occurrance_prob)

    def __sub__(self, value: float) -> "Event":
        return Event(self.amount_dist - value, self.occurrance, self.occurrance_prob)

    def __mul__(self, value: float) -> "Event":
        return Event(self.amount_dist * value, self.occurrance, self.occurrance_prob)

    def __truediv__(self, value: float) -> "Event":
        return Event(self.amount_dist / value, self.occurrance, self.occurrance_prob)

    def __str__(self):
        return f'Event(occurrance={self.occurrance}, prob={self.occurrance_prob}, amount={self.amount_dist})'

class FixedDayEvent(Event):
    """An event that occurs on a fixed day of the month with a fixed amount"""
    day: int

    def __init__(self, amount: float|int|Distribution, occurrance: EventOccurrance|None = None, occurrance_prob: float|None = None,
        day: int|None = None, monthly: float|None = None, daily: float|None = None, weekly: float|None = None
    ):
        super().__init__(amount, occurrance=occurrance, occurrance_prob=occurrance_prob, monthly=monthly, daily=daily, weekly=weekly)
        if day is not None:
            self.day = day
        elif monthly is not None:
            self.day = random_module.randint(1, 28)
        elif weekly is not None:
            self.day = random_module.randint(1, 7)
        elif daily is not None:
            self.day = 1

    def __str__(self):
        return f'FixedDayEvent(day={self.day}, occurrance={self.occurrance}, prob={self.occurrance_prob}, amount={self.amount_dist})'

class Weights:
    events: dict[str, Event]

    def __init__(self, values: dict[str, Event]):
        self.events = values

    def update(self, values: dict[str, Event], inplace=True) -> "Weights":
        if inplace:
            self.events.update(values)
            return self
        return Weights({**self.events, **values})

    def __getitem__(self, key: str|list[str]) -> "Weights":
        if isinstance(key, str):
            return Weights({key: self.events[key]})
        elif isinstance(key, list):
            return Weights({k: self.events[k] for k in key})
        else:
            raise ValueError('Key must be a string or a list of strings')

    def __setitem__(self, key: str, value: Event):
        self.events[key] = value

    def __iter__(self) -> Iterable[str]:
        return iter(self.events)

    def __and__(self, other: "Weights") -> "Weights":
        return self.update(other.events, inplace=False)

    # Arithmetic operations

    def __add__(self, value: float) -> "Weights":
        return Weights({
            key: event + value
            for key, event in self.events.items()
        })

    def __sub__(self, value: float) -> "Weights":
        return Weights({
            key: event - value
            for key, event in self.events.items()
        })

    def __mul__(self, value: float) -> "Weights":
        return Weights({
            key: event * value
            for key, event in self.events.items()
        })

    def __truediv__(self, value: float) -> "Weights":
        return Weights({
            key: event / value
            for key, event in self.events.items()
        })

    # Utility methods
    def __str__(self):
        val = 'Weigths'
        for k, v in self.events.items():
            val += f'\n  {k}: {v}'
        return val
