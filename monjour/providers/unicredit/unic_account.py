import pandas as pd

from monjour.core.merge import Merger
from monjour.core.archive import Archive, ArchiveID
from monjour.core.config import Config
from monjour.core.importer import Importer, ImporterInfo
from monjour.utils.locale_importer import with_locale_helper

from monjour.providers.generic.bank_account import BankAccount
from monjour.providers.unicredit.unic_types import UnicreditCategory, UnicreditTransaction

@with_locale_helper()
class Unicredit(BankAccount):
    """
    Class representing a Unicredit account.
    It doesn't necessarily have to refer to a bank account, it could also refer to a credit card,
    prepaid card, etc. Anything that uses the same unicredit csv format.
    """
    currency: str|None

    PROVIDER_ID = 'unicredit'
    TRANSACTION_TYPE = UnicreditTransaction
    COLUMN_ORDER = [
        'date', 'amount', 'currency', 'unicredit_category', 'counterpart', 'location',
        'desc', 'payment_type', 'payment_type_details', 'extra', 'unicredit_original_desc', 'unicredit_registration_date', 'unicredit_id'
    ]

    def __init__(
        self,
        id:         str,
        iban:       str|None = None,
        name:       str|None = None,
        locale:     str|None = None,
        currency:   str|None = None,
        card_last_4_digits: str|None = None,
        importer:   Importer|None = None,
        merger:     Merger|None = None,
        **kwargs
    ):
        super().__init__(id, name, locale, iban, card_last_4_digits, importer,
                         merger, currency=currency, **kwargs)
        self.currency = currency

    def initialize(self, config: Config) -> None:
        super().initialize(config)
        if self.currency is None:
            self.currency = config.currency

    ##############################################
    # Override methods
    ##############################################

    def get_default_merger(self) -> Merger:
        from monjour.providers.unicredit.unic_merger import merge_unicredit
        return merge_unicredit

