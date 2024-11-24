from typing import Mapping
from dataclasses import fields, field, dataclass
from gen.events import Event

from gen.common import *

class Weights:
    map: Mapping[str, Event]

    def __init__(self, map: Mapping[str, Event]):
        self.map = map

    # Allow to create a copy of weights with syntax weights[['key1', 'key2']]
    def __getitem__(self, keys):
        return Weights({ k: v for k, v in self.map.items() if k in keys })

    # Allow to create a copy of weights with syntax weights + other_weights
    def __add__(self, other: Self|Mapping[str, Event]):
        if isinstance(other, Mapping):
            return Weights({ **self.map, **other })
        elif isinstance(other, Weights):
            return Weights({ **self.map, **other.map })
        raise ValueError('Invalid type')

@dataclass
class Life:
    weights: Weights
    protagonist: Person
    parent: Person
    location: str
    currency: str

    @classmethod
    def copy_from(cls, _from: "Life", **extra):
        args = { field.name: getattr(_from, field.name) for field in fields(_from) if field not in extra }
        return cls(**args, **extra)

    def __init__(self, protagonist: Person, weights: Weights, location: str, currency: str):
        self.protagonist = protagonist
        self.weights = weights
        self.location = location
        self.currency = currency

    def restaurant_name(self):
        return faker.company()

    def supermaket_name(self):
        return f'Supermaket {faker.company()} {self.location}'

    def online_retailer(self):
        return 'Amazon' if random() < 0.5 else faker.company()

@dataclass
class RoutineLife(Life):
    gym_name: str = field(init=False)
    _preferred_restaurants: list[str] = field(init=False)
    _preferred_supermaket: list[str] = field(init=False)

    def __post_init__(self):
        self._preferred_restaurants = [ super().restaurant_name() for _ in range(5)]
        self._preferred_supermaket = [ super().supermaket_name() for _ in range(3) ]
        self.gym_name = f'{faker.company()} Gym'

    def restaurant_name(self):
        return randlist(self._preferred_restaurants) if random() < 0.7 else super().restaurant_name()

    def supermaket_name(self):
        return randlist(self._preferred_supermaket) if random() < 0.7 else super().supermaket_name()

@dataclass
class RentLife(RoutineLife):
    landlord: Person

@dataclass
class UniLife(RentLife):
    pass

@dataclass
class WorkLife(RentLife):
    employer_name: str