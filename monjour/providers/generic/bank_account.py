from enum import Enum

from monjour.core.account import Account
from monjour.core.importer import Importer
from monjour.core.transaction import Transaction
from monjour.core.merge import MergerFn

class BankAccount(Account):
    """
    Small extension of the Account class for bank accounts that have an IBAN or card number.
    This is an abstract class. If you want to create a generic bank account, use the GenericBankAccount class.
    """

    iban: str|None
    card_last_4_digits: str|None

    def __init__(
        self,
        id: str,
        name: str|None = None,
        locale: str|None = None,
        iban: str|None = None,
        card_last_4_digits: str|None = None,
        importer: Importer|None = None,
        merger: MergerFn|None = None,
    ):
        super().__init__(id, name=name, locale=locale, importer=importer, merger=merger)
        self.iban = iban
        self.card_last_4_digits = card_last_4_digits

class GenericBankAccount(BankAccount):
    PROVIDER_NAME = 'generic_bank'
