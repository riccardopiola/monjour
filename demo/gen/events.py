import random as random_module
from typing import Literal

from gen.random import Distribution, constant, uniform, normal

class Event:
    probability: float
    distribution: Distribution

    def __init__(self, distribution: Distribution, probability: float):
        self.distribution = distribution
        self.probability = probability

    @property
    def amount(self) -> float:
        return self.distribution()

class RoutineEvent(Event):
    occurrance: Literal['daily', 'weekly', 'monthly']

    def __init__(self, distribution: Distribution,
                 daily: float|None = None, weekly: float|None = None, monthly: float|None = None):
        if daily is not None:
            probability = daily
            self.occurrance = 'daily'
        elif weekly is not None:
            probability = weekly
            self.occurrance = 'weekly'
        elif monthly is not None:
            probability = monthly
            self.occurrance = 'monthly'
        else:
            raise ValueError('One of daily, weekly or monthly must be provided')
        super().__init__(distribution, probability)

    def daily_probability(self) -> float:
        match self.occurrance:
            case 'daily':
                return self.probability
            case 'weekly':
                return self.probability / 7
            case 'monthly':
                return self.probability / 30
            case _:
                raise ValueError('Unknown occurance')

    def weekly_probability(self) -> float:
        match self.occurrance:
            case 'daily':
                return self.probability * 7
            case 'weekly':
                return self.probability
            case 'monthly':
                return self.probability / 4
            case _:
                raise ValueError('Unknown occurance')

    def monthly_probability(self) -> float:
        match self.occurrance:
            case 'daily':
                return self.probability * 30
            case 'weekly':
                return self.probability * 4
            case 'monthly':
                return self.probability
            case _:
                raise ValueError('Unknown occurance')

class MonthlyFixture(Event):
    day: int

    def __init__(self, amount: int|float, day: int|None = None):
        super().__init__(constant(amount), 1.0)
        self.day = day or random_module.randint(1, 28)
        assert self.day > 0 and self.day <= 28
