import pandas as pd

from lib.core.account import BankAccount
from lib.core.merge import MergerFn
from lib.core.archive import Archive, ArchiveID
from lib.core.config import Config
from lib.core.importer import Importer

from lib.providers.unicredit.unic_categories import UnicreditCategory

class Unicredit(BankAccount):
    """
    Class representing a Unicredit account.
    It doesn't necessarily have to refer to a bank account, it could also refer to a credit card,
    prepaid card, etc. Anything that uses the same unicredit csv format.
    """
    currency: str|None

    PROVIDER_ID = 'unicredit'
    DF_COLUMNS = BankAccount.DF_COLUMNS | {
        'unicredit_id': pd.Series([], dtype='string'),
        'unicredit_category': pd.Categorical([], categories=[c.value for c in UnicreditCategory]),
        'unicredit_original_desc': pd.Series([], dtype='string'),
    } # type: ignore
    DTYPES = { k: v.dtype for k, v in DF_COLUMNS.items() }

    def __init__(
        self,
        id:         str,
        iban:       str|None = None,
        name:       str|None = None,
        locale:     str|None = None,
        currency:   str|None = None,
        card_last_4_digits: str|None = None,
        importer:   Importer|None = None,
        merger:     MergerFn|None = None,
    ):
        super().__init__(id, name=name, iban=iban, locale=locale, card_last_4_digits=card_last_4_digits, importer=importer, merger=merger)
        self.currency = currency

    def initialize(self, config: Config, archive: Archive) -> None:
        super().initialize(config, archive)
        if self.currency is None:
            self.currency = config.currency

    ##############################################
    # Override methods
    ##############################################

    def get_default_importer(self, locale: str|None) -> Importer:
        from lib.providers.unicredit.importers import get_importer_for_locale
        return get_importer_for_locale(self, locale)

    def get_default_merger(self) -> MergerFn:
        from lib.providers.unicredit.unic_merger import merge_unicredit
        return merge_unicredit
