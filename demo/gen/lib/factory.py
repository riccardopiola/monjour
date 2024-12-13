from datetime import datetime

from .api import Transaction, PaymentType, Expenses, Income
from .life import Life, WorkLife, UniLife, RoutineLife
from .common import BANK, PAYPAL, faker

######################################
# Daily
######################################

def coffee(life: Life, date, amount: float):
    restaurant_name = life.restaurant_name()
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Coffee',
        counterpart=restaurant_name,
        location=life.location,
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Food
    )

def restaurant(life: Life, date, amount: float):
    restaurant_name = life.restaurant_name()
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Lunch at ' + restaurant_name,
        counterpart=restaurant_name,
        location=life.location,
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Food
    )

def transport(life: Life, date, amount: float):
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Public Transport',
        counterpart=life.location + ' Transport Company',
        location=life.location,
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Transport
    )

######################################
# Weekly
######################################

def online_purchase(life: Life, date: datetime, amount: float) -> Transaction:
    company = life.online_retailer()
    return Transaction(
        account_id=PAYPAL,
        date=date,
        amount=-amount,
        currency='EUR',
        desc='Order at ' + company,
        counterpart=company,
        location='Online',
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Shopping
    )

def withdrawal(life: Life, date, amount: float):
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='ATM Withdrawal',
        counterpart=None,
        location=life.location,
        payment_type=PaymentType.Withdrawal,
        category=Expenses.Other
    )

def night_out(life: Life, date: datetime, amount: float) -> Transaction:
    restaurant_name = life.restaurant_name()
    return Transaction(
        account_id='bank',
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Night Out at ' + restaurant_name,
        counterpart=restaurant_name,
        location=life.location,
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Entertainment
    )

def groceries(life: Life, date, amount: float) -> Transaction:
    supermarket = life.supermaket_name()
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Payment at ' + supermarket,
        counterpart=supermarket,
        location=life.currency,
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Groceries
    )

######################################
# Occational (Monthly)
######################################

def book_purchase(life: Life, date: datetime, amount: float) -> Transaction:
    return Transaction(
        account_id=PAYPAL,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Book Purchase',
        counterpart=faker.company(),
        location='Online',
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=Expenses.Education
    )

######################################
# Subscriptions
######################################

def _make_subscription(life: Life, date, company: str, amount: float, category = Expenses.Entertainment):
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc=f'{company} Subscription',
        counterpart=company,
        location=life.location,
        payment_type=PaymentType.CardPayment,
        payment_type_details=life.protagonist.get_card_payment_details(),
        category=category
    )

def netflix_subscription(life: Life, date: datetime, amount: float) -> Transaction:
    return _make_subscription(life, date, 'Netflix', amount, Expenses.Entertainment)

def spotify_subscription(life: Life, date: datetime, amount: float) -> Transaction:
    return _make_subscription(life, date, 'Spotify', amount, Expenses.Entertainment)

def amazon_prime_subscription(life: Life, date: datetime, amount: float) -> Transaction:
    return _make_subscription(life, date, 'Amazon Prime', amount, Expenses.Entertainment)

def phone_subscription(life: Life, date: datetime, amount: float) -> Transaction:
    return _make_subscription(life, date, 'Phone', amount, Expenses.Bills)

def interest(life: Life, date: datetime, amount: float) -> Transaction:
    return Transaction(
        account_id=BANK,
        date=date,
        amount=amount,
        currency=life.currency,
        desc='Interest',
        counterpart=None,
        location=None,
        payment_type=PaymentType.Transfer,
        ref=None,
        category=Income.Interest
    )

######################################
# RoutineLife
######################################

def gym_membership(life: RoutineLife, date: datetime, amount: float) -> Transaction:
    return _make_subscription(life, date, life.gym_name, amount, Expenses.Health)

def rent(life: UniLife, date: datetime, amount: float) -> Transaction:
    return Transaction(
        account_id=BANK,
        date=date,
        amount=-amount,
        currency=life.currency,
        desc='Monthly Rent',
        counterpart=life.landlord.fullname(),
        location=None,
        payment_type=PaymentType.Transfer,
        ref=life.landlord.get_iban_ref(),
        category=Expenses.Housing
    )

######################################
# UniLife
######################################

def allowance(life: UniLife, date: datetime, amount: float) -> Transaction:
    return Transaction(
        account_id=BANK,
        date=date,
        amount=amount,
        currency=life.currency,
        desc='Allowance',
        counterpart=life.parent.fullname(),
        location=None,
        payment_type=PaymentType.Transfer,
        ref=life.parent.get_iban_ref(),
        category=Income.Other
    )

######################################
# WorkLife
######################################

def salary(life: WorkLife, date: datetime, amount: float) -> Transaction:
    return Transaction(
        account_id=BANK,
        date=date,
        amount=amount,
        currency=life.currency,
        desc='Salary',
        counterpart=life.employer_name,
        location=life.location,
        payment_type=PaymentType.Transfer,
        ref=None,
        category=Income.Salary
    )
