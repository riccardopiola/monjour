from abc import ABC, abstractmethod
from pathlib import Path
from typing import IO, Callable
import pandas as pd

import monjour.core.log as log
from monjour.core.archive import Archive, ArchiveID
from monjour.core.common import DateRange
from monjour.core.config import Config
from monjour.core.importer import ImportContext, Importer
from monjour.core.merge import MergeContext, MergerFn

# Columns that will always be present in the Account DataFrame
ACCOUNT_COLUMNS = {
    'date':             pd.Series([], dtype='datetime64[s]'),
    'amount':           pd.Series([], dtype='float64'),
    'currency':         pd.Series([], dtype='string'),
    'desc':             pd.Series([], dtype='string'),
    'archive_id':       pd.Series([], dtype='string'),
    'category':         pd.Series([], dtype='string'),
    'counterpart':      pd.Series([], dtype='string'),
}

# Columns that will always be present in the BankAccount DataFrame
BANK_ACCOUNT_COLUMNS = ACCOUNT_COLUMNS | {
    'payment_details':  pd.Series([], dtype='string'),
    'location':         pd.Series([], dtype='string'),
}

class Account(ABC):
    """
    Base class representing any list of transactions.
    It is a thin wrapper around a DataFrame that also contains additional logic for:
    - Importing new files (or deferring the import to an Importer object)
    - Merging the data into a master DataFrame.

    NOTE: initialize() is separated from __init__ to allow the account to be defined before the
    archive is created and without manually passing the global config around.
    If initialize() is not called, the account object should not be used.

    Attributes:
        id:         Unique identifier for the account.
        data:       DataFrame containing the transactions.
        name:       Optional readable name for the account.
        locale:     Optional locale for the account.
        importer:   Optional importer to use to import new files into this account. If not provided,
                    the importer will be automatically selected based on the locale.

        PROVIDER_ID:    Unique identifier for the provider of the account.
        DF_COLUMNS:     Columns that should be present in the DataFrame.
        DTYPES:         Dictionary of column names and their corresponding dtypes.
    """

    id: str
    data: pd.DataFrame
    name: str|None
    config: Config
    locale: str|None
    _importer: Importer|None
    _merger: MergerFn|None

    # Should be overridden by subclasses
    PROVIDER_ID = 'generic'
    DF_COLUMNS: dict[str, pd.Series] = ACCOUNT_COLUMNS
    DTYPES: dict[str, str] = { k: v.dtype for k, v in ACCOUNT_COLUMNS.items() }

    ##############################################
    # Initialization
    ##############################################

    def __init__(
        self,
        id: str,
        name: str|None = None,
        locale: str|None = None,
        importer: Importer|None = None,
        merger: MergerFn|None = None,
    ):
        self.id = id
        self.name = name
        self.locale = locale
        self._importer = importer
        self._merger = merger
        self.data = pd.DataFrame(self.DF_COLUMNS)

    def initialize(self, config: Config, archive: Archive):
        """
        Initialize the account with the provided config by loading the data from the archive.
        This function is called by the App object right after the account is defined.
        """
        self.config = config
        if self.locale is None:
            self.locale = config.locale
        if self.currency is None:
            self.currency = config.currency
        self.load_all_from_archive(archive)

    @property
    def importer(self) -> Importer:
        if self._importer is None:
            self._importer = self.get_default_importer(self.locale)
        return self._importer

    @property
    def merger(self) -> MergerFn:
        if self._merger is None:
            self._merger = self.get_default_merger()
        return self._merger

    def merge(self, ctx: MergeContext) -> pd.DataFrame:
        """
        Merge the account data into another DataFrame.
        This method is usually called by App when it merges all the accounts into a single DataFrame.

        The Account class implementing this method is resposible for performing any join or merge operation
        that is necessary to combine the account data with the other DataFrame.

        Args:
            other: DataFrame to merge the account data into.
        """
        return self.merger(ctx, self.data)

    ##############################################
    # Abstract methods
    ##############################################

    @abstractmethod
    def get_default_merger(self) -> MergerFn:
        """
        Merge the account data into another DataFrame.
        This method is usually called by App when it merges all the accounts into a single DataFrame.

        The Account class implementing this method is resposible for performing any join or merge operation
        that is necessary to combine the account data with the other DataFrame.

        Args:
            other: DataFrame to merge the account data into.
        """
        ...

    @abstractmethod
    def get_default_importer(self, locale: str|None) -> Importer:
        """
        Get the importer to use for the account based on the locale.
        If no importer is defined and no locale is provided, an exception will be raised.
        """
        ...

    ##############################################
    # Importing (defers to the Importer)
    ##############################################

    def import_file(self, archive: Archive, file: Path, date_range: DateRange):
        # Use the importer to read the file into a dataframe
        importer = self.importer
        with open(file, 'rb') as f:
            archive_id = archive.calculate_archive_id(self.id, date_range)
            import_context = ImportContext(self, archive, archive_id, date_range)
            df = importer.import_file(import_context, f)

        # Register with the archive that we are using an external file
        archive.register_file(self.id, importer.info, date_range, file)
        self.data = pd.concat([self.data, df])

    def archive_file(self, archive: Archive, buffer: IO[bytes],
                     filename: str, date_range: DateRange):
        # Use the importer to read the file into a dataframe
        importer = self.importer
        archive_id = archive.calculate_archive_id(self.id, date_range)
        import_context = ImportContext(self, archive, archive_id, date_range)
        df = importer.import_file(import_context, buffer)

        # Save the file in the archive
        ext = filename.split('.')[-1]
        archive.archive_file(self.id, importer.info, date_range, buffer, ext)

        # Merge the new data into the account
        self.data = pd.concat([self.data, df])

    def load_from_archive(self, archive: Archive, archive_id: ArchiveID, check_hash=False):
        """
        Load a file from the archive into the account.

        Args:
            archive:    Archive object to use for loading the file.
            archive_id: ID of the file in the archive.
            check_hash: If True, the hash of the file will be checked before loading.
        """
        # Use the importer to read the file into a dataframe
        date_range = archive.get_date_range(archive_id)
        buf = archive.load_file(archive_id, check_hash=check_hash)
        import_context = ImportContext(self, archive, archive_id, date_range)
        df = self.importer.import_file(import_context, buf)
        # Merge the new data into the account
        self.data = pd.concat([self.data, df])

    def load_all_from_archive(self, archive: Archive, check_hash: bool=False):
        """
        Load all the files from the archive that belong to the account.
        """
        # Read all the files from the archive with the importer
        dfs = []
        archive_records = archive.get_records_for_account(self.id)
        for record in archive_records:
            date_range = DateRange(record['date_start'], record['date_end'])
            buf = archive.load_file(record['id'], check_hash=check_hash)
            import_context = ImportContext(self, archive, record['id'], date_range)
            df = self.importer.import_file(import_context, buf)
            dfs.append(df)

        # Merge all the new data into the account
        self.data = pd.concat([self.data] + dfs)

class BankAccount(Account):
    """
    Small extension of the Account class for bank accounts that have an IBAN or card number.
    """

    iban: str|None
    card_last_4_digits: str|None

    PROVIDER_NAME = 'generic_bank'
    DF_COLUMNS = BANK_ACCOUNT_COLUMNS
    DTYPES = { k: v.dtype for k, v in BANK_ACCOUNT_COLUMNS.items() }

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