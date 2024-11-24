from gen.common import *
from gen.life import *

class Factory:
    life: Life

    def __init__(self, life: Life):
        self.life = life

    ######################################
    # Daily
    ######################################

    def coffee(self, date, amount: float):
        restaurant_name = self.life.restaurant_name()
        return Transaction(
            account_id=BANK,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='Coffee',
            counterpart=restaurant_name,
            location=self.life.location,
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Food
        )

    def restaurant(self, date, amount: float):
        restaurant_name = self.life.restaurant_name()
        return Transaction(
            account_id=BANK,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='Lunch at ' + restaurant_name,
            counterpart=restaurant_name,
            location=self.life.location,
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Food
        )

    def transport(self, date, amount: float):
        return Transaction(
            account_id=BANK,
            date=date,
            amount=amount,
            currency=self.life.currency,
            desc='Public Transport',
            counterpart=self.life.location + ' Transport Company',
            location=self.life.location,
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Transport
        )

    ######################################
    # Weekly
    ######################################

    def online_purchase(self, date: datetime, amount: float) -> Transaction:
        company = self.life.online_retailer()
        return Transaction(
            account_id=PAYPAL,
            date=date,
            amount=-amount,
            currency='EUR',
            desc='Order at ' + company,
            counterpart=company,
            location='Online',
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Shopping
        )

    def withdrawal(self, date, amount: float):
        return Transaction(
            account_id=BANK,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='ATM Withdrawal',
            counterpart=None,
            location=self.life.location,
            payment_type=PaymentType.Withdrawal,
            category=Expenses.Other
        )

    def night_out(self, date: datetime, amount: float) -> Transaction:
        restaurant_name = self.life.restaurant_name()
        return Transaction(
            account_id='bank',
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='Night Out at ' + restaurant_name,
            counterpart=restaurant_name,
            location=self.life.location,
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Entertainment
        )

    def groceries(self, date, amount: float) -> Transaction:
        supermarket = self.life.supermaket_name()
        return Transaction(
            account_id=BANK,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='Payment at ' + supermarket,
            counterpart=supermarket,
            location=self.life.currency,
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Groceries
        )

    ######################################
    # Occational (Monthly)
    ######################################

    def book_purchase(self, date: datetime, amount: float) -> Transaction:
        return Transaction(
            account_id=PAYPAL,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='Book Purchase',
            counterpart=faker.company(),
            location='Online',
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=Expenses.Education
        )

    ######################################
    # Subscriptions
    ######################################

    def _make_subscription(self, date, company: str, amount: float, category = Expenses.Entertainment):
        return Transaction(
            account_id=BANK,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc=f'{company} Subscription',
            counterpart=company,
            location=self.life.location,
            payment_type=PaymentType.CardPayment,
            payment_type_details=self.life.protagonist.get_card_payment_details(),
            category=category
        )

    def netflix_subscription(self, date: datetime, amount: float) -> Transaction:
        return self._make_subscription(date, 'Netflix', amount, Expenses.Entertainment)

    def spotify_subscription(self, date: datetime, amount: float) -> Transaction:
        return self._make_subscription(date, 'Spotify', amount, Expenses.Entertainment)

    def amazon_prime_subscription(self, date: datetime, amount: float) -> Transaction:
        return self._make_subscription(date, 'Amazon Prime', amount, Expenses.Entertainment)

    def phone_subscription(self, date: datetime, amount: float) -> Transaction:
        return self._make_subscription(date, 'Phone', amount, Expenses.Bills)

class RoutineFactory(Factory):
    life: RoutineLife

    def gym_membership(self, date: datetime, amount: float) -> Transaction:
        return self._make_subscription(date, self.life.gym_name, amount, Expenses.Health)

class UniFactory(RoutineFactory):
    life: UniLife

    def rent(self, date: datetime, amount: float) -> Transaction:
        return Transaction(
            account_id=BANK,
            date=date,
            amount=-amount,
            currency=self.life.currency,
            desc='Monthly Rent',
            counterpart=self.life.landlord.fullname(),
            location=None,
            payment_type=PaymentType.Transfer,
            ref=self.life.landlord.get_iban_ref(),
            category=Expenses.Housing
        )

    def allowance(self, date: datetime, amount: float) -> Transaction:
        return Transaction(
            account_id=BANK,
            date=date,
            amount=amount,
            currency=self.life.currency,
            desc='Allowance',
            counterpart=self.life.parent.fullname(),
            location=None,
            payment_type=PaymentType.Transfer,
            ref=self.life.parent.get_iban_ref(),
            category=Income.Other
        )

class WorkFactory(RoutineFactory):
    life: WorkLife

    def salary(self, date: datetime, amount: float) -> Transaction:
        return Transaction(
            account_id=BANK,
            date=date,
            amount=amount,
            currency=self.life.currency,
            desc='Salary',
            counterpart=self.life.employer_name,
            location=self.life.location,
            payment_type=PaymentType.Transfer,
            ref=None,
            category=Income.Salary
        )
