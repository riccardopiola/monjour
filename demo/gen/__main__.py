import os
from pathlib import Path

from gen.common import *
from gen.period1 import *
from gen.life import *

OUT_DIR = Path (os.path.dirname(__file__)) / 'out'

protagonist = Person(
    name='John',
    surname='Doe',
    iban='IT00X0000000000000000000000',
    email='john@doe.com',
    card_number='1234'
)

uni_weights = Weights({
    'coffee'              : RoutineEvent(constant(2), daily=0.4),
    'withdrawal'          : RoutineEvent(normal(50, 10), daily=0.15),
    'online_purchase'     : RoutineEvent(normal(50, 10), daily=0.1),
    'transport'           : RoutineEvent(normal(2, 0.5), daily=1.0),

    'groceries'           : RoutineEvent(normal(40, 10), weekly=0.8),
    'night_out'           : RoutineEvent(constant(50), weekly=0.2),

    'book_purchase'       : RoutineEvent(normal(20, 5), monthly=0.5),

    'rent'                : MonthlyFixture(500),
    'gym_membership'      : MonthlyFixture(30),
    'phone_subscription'  : MonthlyFixture(10),
    'allowance'           : MonthlyFixture(200)
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