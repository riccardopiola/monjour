"""
In this file we define the configuration of the application.
"""
from monjour.prelude import *
from monjour.providers.generic import BankAccount
from monjour.providers.generic.importers.csv_importer import CSVImporter

from demo_app import DemoApp

##############################################
# General configuration
##############################################

# These should match what is defined in demo.gen.__main__.py
app = DemoApp(
    Config(
        name="John",
        surname="Doe",
        currency="EUR",
        locale="it_IT",
        time_zone="Europe/Rome",
        appdata_dir="./appdata",
    )
)

##############################################
# Balance sheet definitions
##############################################

app.define_accounts(
    BankAccount(
        id='bank',
        name='Checking account',
        iban='IT00X0000000000000000000000',
        card_last_4_digits='1234',
        importer=CSVImporter()
    ),
    Account(
        id='paypal',
        name='Paypal Account',
        importer=CSVImporter()
    ),
)

##############################################
# Category definitions
##############################################

app.define_categories(
    Category('Income/Salary',           '💰'),
    Category('Income/Gift',             '🎁'),
    Category('Income/Other',            '💸'),

    Category('Expense/Food',            '🍔'),
    Category('Expense/Groceries',       '🛒'),
    Category('Expense/Housing',         '🏠'),
    Category('Expense/Bills',           '💡'),
    Category('Expense/Transport',       '🚗'),
    Category('Expense/Entertainment',   '🎬'),
    Category('Expense/Health',          '🏥'),
    Category('Expense/Shopping',        '🛍️'),
    Category('Expense/Travel',          '✈️'),
    Category('Expense/Gift',            '🎁'),
    Category('Expense/Education',       '📚'),
    Category('Expense/Other',           '💸'),
)

##############################################
# Rules
##############################################

app.import_file('bank', './gen/out/bank_2021.csv')
app.import_file('paypal', './gen/out/paypal_2021.csv')