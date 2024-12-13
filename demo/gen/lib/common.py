from dataclasses import dataclass
from faker import Faker
from datetime import datetime, timedelta, date
from random import random, randrange, randint
from typing import Callable
import statistics

from .api import Transaction, PaymentType, Expenses, Income

PAYPAL = 'paypal'
BANK = 'bank'

# Define a seed
SEED = 0
Faker.seed(SEED)
faker = Faker()

@dataclass
class Person:
    name: str
    surname: str
    iban: str
    email: str
    card_number: str # last 4 digits

    @classmethod
    def random(cls):
        return cls(
            faker.first_name(), faker.last_name(), faker.iban(), faker.email(), faker.credit_card_number()[15:]
        )

    def fullname(self):
        return f'{self.name} {self.surname}'

    def get_card_payment_details(self):
        return f'card:{self.card_number}'

    def get_iban_ref(self):
        return f'iban:{self.iban}'

# Utilities for Randomness
def random_date(start: datetime, end: datetime) -> datetime:
    return start + timedelta(seconds=randrange(int((end - start).total_seconds())))

def randlist(ls: list):
    return ls[randrange(len(ls))]

def random_norm(avg: float|int, stddev: float|int) -> float:
    return statistics.NormalDist(float(avg), float(stddev)).inv_cdf(random())

def get_month_daterange(year: int, month: int) -> tuple[datetime, datetime]:
    if month < 12:
        return datetime(year, month, 1), datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        return datetime(year, 12, 1), datetime(year, 12, 31)
