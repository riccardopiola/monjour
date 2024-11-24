from abc import ABC, abstractmethod
import random as random_module
from functools import partial

from gen.common import *
from gen.factory import Weights, Factory
from gen.life import Life
from gen.events import Event, RoutineEvent, MonthlyFixture

class Routine(ABC):
    # Start(Included), End (Not included)
    life: Life
    factory: Factory

    date_range: tuple[datetime, datetime]
    today: datetime

    _daily_events: list[Callable] = []
    _weekly_events: list[Callable] = []
    _monthly_events: list[Callable] = []

    trn: TransactionList

    def __init__(self, date_range: tuple[datetime, datetime], life: Life, factory: Factory):
        assert date_range[0] < date_range[1]
        self.date_range = date_range
        self.today = date_range[0]
        self.trn = TransactionList()
        self.life = life
        self.factory = factory
        self._update_events()

    def _update_events(self):
        for event_name, event in self.life.weights.map.items():
            factory_func: Callable[[datetime, float], Transaction] = getattr(self.factory, event_name)
            if isinstance(event, RoutineEvent):
                if event.occurrance == 'daily':
                    self._daily_events.append(partial(self._run_daily_event, event, factory_func))
                elif event.occurrance == 'weekly':
                    self._weekly_events.append(partial(self._run_weekly_event, event, factory_func))
                elif event.occurrance == 'monthly':
                    self._monthly_events.append(partial(self._run_monthly_event, event, factory_func))
            elif isinstance(event, MonthlyFixture):
                self._monthly_events.append(partial(self._run_monthly_fixture, event, factory_func))

    def _run_daily_event(self, event: RoutineEvent, fn: Callable[[datetime, float], Transaction]):
        if random_module.random() < event.probability:
            self.trn += fn(self.today, event.amount)

    def _run_weekly_event(self, event: RoutineEvent, fn: Callable[[datetime, float], Transaction]):
        if random_module.random() < event.probability:
            self.trn += fn(random_date(*self.this_week_daterange()), event.amount)

    def _run_monthly_event(self, event: RoutineEvent, fn: Callable[[datetime, float], Transaction]):
        if random_module.random() < event.probability:
            self.trn += fn(random_date(*self.this_month_daterange()), event.amount)

    def _run_monthly_fixture(self, event: MonthlyFixture, fn: Callable[[datetime, float], Transaction]):
        day = datetime(self.year, self.month, event.day)
        self.trn += fn(day, event.amount)

    def update(self, life: Life):
        self.life = life
        self.factory = Factory(life)
        self._update_events()

    @property
    def year(self):
        return self.today.year

    @property
    def month(self):
        return self.today.month

    @staticmethod
    def get_next_month(start: datetime) -> datetime:
        """Returns a datetime object for the first day of month following to the given date"""
        if start.month == 12:
            return datetime(start.year + 1, 1, 1)
        return datetime(start.year, start.month + 1, 1)

    def this_week_daterange(self) -> tuple[datetime, datetime]:
        start = self.today
        end = start + timedelta(days=7)
        if self.date_range[1] < end:
            return start, self.date_range[1]
        return start, end

    def this_month_daterange(self) -> tuple[datetime, datetime]:
        start = self.today
        next_month = self.get_next_month(start)
        if self.date_range[1] < next_month:
            return start, self.date_range[1]
        return start, next_month

    def log_day(self):
        print("{} - Generating day".format(self.today.strftime('%Y-%m-%d')))
    def log_week(self):
        end = self.today + timedelta(days=7)
        print("{} - {} - Generating week".format(self.today.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))
    def log_month(self):
        start, end = self.this_month_daterange()
        print("{} - {} - Generating month".format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))

    ########################################################
    # Generation methods
    ########################################################

    def gen_day(self):
        """Generate transactions for a day. Advances the current_day by 1 day."""
        self.log_day()
        for event in self._daily_events:
            event()
        self.today += timedelta(days=1)

    def gen_week(self):
        """Generate transaction for a week. Advances the current_day by 7 days."""
        self.log_week()
        assert self.today.weekday() == 0
        for event in self._weekly_events:
            event()
        for _ in range(0, 7):
            self.gen_day()

    def gen_period(self, start: datetime, end: datetime):
        """
        Generate transactions for a period.
        Advances the current_day to the end of the period.

        Args:
            start: datetime (Included)
            end: datetime (Not included)
        """
        print("{} - {} - Generating period".format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))

        # Fill in the starting days of the week
        while self.today.weekday() != 0:
            self.gen_day()

        # Weekly transactions
        while self.today <= (end - timedelta(days=7)):
            self.gen_week()

        # Fill in the ending days of the week
        while self.today != end:
            self.gen_day()

        assert self.today == end

    def gen_month(self, monthly_events_override: bool = False):
        """
        Generates a month of transactions. Advances the first day of the next month (not processed)

        Monthly events will only be processed if self.today is the first day of the month or if
        monthly_events_override is set to True.
        """
        start, end = self.this_month_daterange()
        if monthly_events_override or self.today.day == 1:
            for event in self._monthly_events:
                event()
        self.gen_period(start, end) # advances current day
        assert self.today == self.date_range[1] or self.today.day == 1
        self.log_month()

    def run(self, first_month_events: bool = True) -> TransactionList:
        while self.today < self.date_range[1]:
            self.gen_month(first_month_events)
            if first_month_events: # Just the first month
                first_month_events = False
        return self.trn