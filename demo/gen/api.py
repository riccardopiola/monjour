from enum import Enum
from dataclasses import dataclass
from typing import Optional, Self
from datetime import datetime
import pandas as pd

def _enum_str(enum):
    enum.__str___ = lambda self: self.value
    return enum

@_enum_str
class Income(Enum):
    # Income
    Salary      = 'Income/Salary'
    Gift        = 'Income/Gift'
    Other       = 'Income/Other'

@_enum_str
class Expenses(Enum):
    # Expenses
    Food            = 'Expense/Food'
    Groceries       = 'Expense/Groceries'
    Housing         = 'Expense/Housing'
    Bills           = 'Expense/Bills'
    Transport       = 'Expense/Transport'
    Entertainment   = 'Expense/Entertainment'
    Health          = 'Expense/Health'
    Shopping        = 'Expense/Shopping'
    Travel          = 'Expense/Travel'
    Gift            = 'Expense/Gift'
    Education       = 'Expense/Education'
    Other           = 'Expense/Other'

# Payment Type Enum
@_enum_str
class PaymentType(Enum):
    CardPayment             = 'CardPayment'
    Transfer                = 'Transfer'
    InternalTransfer        = 'InternalTransfer'
    Refund                  = 'Refund'
    Withdrawal              = 'Withdrawal'
    Deposit                 = 'Deposit'
    PreauthorizedDebit      = 'PreauthorizedDebit'

# Transaction Class
@dataclass
class Transaction:
    account_id: str  # bank or paypal
    date: datetime
    amount: float
    currency: str
    desc: str = ''

    counterpart:            Optional[str] = None
    location:               Optional[str] = None
    payment_type:           Optional[PaymentType] = None
    payment_type_details:   Optional[str] = None
    extra:                  Optional[str] = None  # json = None
    ref:                    Optional[str] = None
    notes:                  Optional[str] = None
    category:               Optional[Expenses|Income] = None

class TransactionList:
    _values: list[Transaction]

    def __init__(self, transactions: list[Transaction]|None = None):
        self._values = transactions or list()
        self._df = None

    def append(self, other: Transaction|list[Transaction]|Self):
        if self._df is None: self._df = None # Invalidate the df

        if isinstance(other, Transaction):
            self._values.append(other)
        elif isinstance(other, TransactionList):
            self._values.extend(other._values)
        elif isinstance(other, list):
            for trn in other:
                self.append(trn)
        else:
            raise ValueError(f'Unsupported type {type(other).__name__}')

    def __iadd__(self, other: Transaction|list[Transaction]|Self):
        self.append(other)
        return self

    def __len__(self):
        return len(self._values)

    def to_df(self) -> pd.DataFrame:
        print('Generating DataFrame')
        if self._df is None:
            self._df = pd.DataFrame([vars(trn) for trn in self._values])
        return self._df