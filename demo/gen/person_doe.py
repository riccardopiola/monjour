import os
from pathlib import Path
from datetime import datetime

from .period1 import UniRoutine
from .lib import *

OUT_DIR = Path (os.path.dirname(__file__)) / 'out'

def main():

    protagonist = Person(
        name='John',
        surname='Doe',
        iban='IT00X0000000000000000000000',
        email='john@doe.com',
        card_number='1234'
    )

    uni_weights = Weights({
        # Daily
        'coffee'              : Event(constant(2), daily=0.2),
        'withdrawal'          : Event(normal(50, 10), daily=0.15),
        'online_purchase'     : Event(normal(50, 10), daily=0.1),
        # Weekly
        'groceries'           : Event(normal(40, 10), weekly=0.8),
        'night_out'           : Event(constant(50), weekly=0.2),
        # Monthly
        'book_purchase'       : Event(normal(20, 5), monthly=0.5),
        # Subscriptions
        'transport'           : FixedDayEvent(22, monthly=1),
        'gym_membership'      : FixedDayEvent(30, monthly=1),
        'phone_subscription'  : FixedDayEvent(10, monthly=1),
        # Expenses
        'rent'                : FixedDayEvent(500, monthly=1),
        # Income
        'allowance'           : FixedDayEvent(200, monthly=1)
    })

    uni_life = UniLife(
        weights=uni_weights,
        protagonist=protagonist,
        parent=Person.random(),
        location='Milan',
        currency='EUR',
        landlord=Person.random()
    )

    trn = TransactionList()
    trn += UniRoutine((datetime(2021, 1, 1), datetime(2022, 1, 1)), uni_life).run()

    work_life = WorkLife.copy_from(uni_life,
        location='London',
        currency='GBP'
    )
    work_life.weights.mul


    # Write the transactions to CSV
    df = trn.to_df()
    OUT_DIR.mkdir(exist_ok=True, parents=True)
    for acc in df['account_id'].unique():
        years = df['date'].dt.year
        acc_df = df[df['account_id'] == acc]
        for year in years.unique():
            filename = OUT_DIR / f'{acc}_{year}.csv'
            print(f'Writing {filename}')
            acc_df[acc_df['date'].dt.year == year].to_csv(filename, index=False)