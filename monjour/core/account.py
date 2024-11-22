from abc import ABC, abstractmethod
from pathlib import Path
from typing import IO, Callable, ClassVar, Self
import pandas as pd

import monjour.core.log as log
from monjour.core.executor import Executor
from monjour.core.archive import Archive, ArchiveID
from monjour.core.common import DateRange
from monjour.core.config import Config
from monjour.core.importer import ImportContext, Importer, ImporterInfo
from monjour.core.merge import MergeContext, Merger, BoundMerger
from monjour.core.transaction import Transaction

class Account(ABC):
    """
    Base class representing any list of transactions.
    It is a thin wrapper around a DataFrame that also contains additional logic for:
    - Importing new files (or deferring the import to an Importer object)
    - Merging the data into a master DataFrame.

    NOTE: initialize() is separated from __init__ to allow the account to be defined before the
    archive is created and without manually passing the global config around.
    If initialize() is not called, the account object should not be used.

    Class Attributes:
        PROVIDER_ID:    Unique identifier for the provider of the account.
        TRANSACTION_TYPE: Type of transactions that the account contains.
        COLUMN_ORDER:   Alternative order for the columns in the DataFrame (for display purpoises).

    Attributes:
        id:         Unique identifier for the account.
        data:       DataFrame containing the transactions.
        name:       Optional readable name for the account.
        locale:     Optional locale for the account.
        importer:   Optional importer to use to import new files into this account. If not provided,
                    the importer will be automatically selected based on the locale.
        merger:     Optional merger to use to merge the account data into the master DataFrame.
    """
    # Should be overridden by subclasses
    PROVIDER_ID: ClassVar[str] = 'generic'
    TRANSACTION_TYPE: ClassVar[type[Transaction]] = Transaction
    COLUMN_ORDER: ClassVar[list[str]] = [ 'date', 'amount', 'currency', 'desc', 'counterpart', 'location' ]

    id: str
    data: pd.DataFrame
    name: str|None
    config: Config
    locale: str|None
    _importer: Importer|None
    _merger: Merger|None

    ##############################################
    # Initialization
    ##############################################

    def __init__(
        self,
        id: str,
        name: str|None = None,
        locale: str|None = None,
        importer: Importer|None = None,
        merger: Merger|None = None,
    ):
        self.id = id
        self.name = name
        self.locale = locale
        self._importer = importer
        self._merger = merger
        self.data = self.TRANSACTION_TYPE.to_empty_df()

    def initialize(self, config: Config):
        """
        Initialize the account with the provided config by loading the data from the archive.
        This function is called by the App object right after the account is defined.
        """
        self.config = config
        if self.locale is None:
            self.locale = config.locale
        if self.currency is None:
            self.currency = config.currency

    @property
    def importer(self) -> Importer:
        if self._importer is None:
            self._importer = self.get_default_importer(self.locale)
        return self._importer

    @property
    def merger(self) -> Merger:
        """
        Merge the account data into another DataFrame.
        This method is usually called by App when it merges all the accounts into a single DataFrame.

        The Account class implementing this method is resposible for performing any join or merge operation
        that is necessary to combine the account data with the other DataFrame.

        Args:
            ctx:   MergeContext object containing the accounts to merge.
            other: DataFrame to merge the account data into.
        """
        if self._merger is None:
            self._merger = self.get_default_merger()
        return self._merger

    ##############################################
    # Merge methods
    ##############################################

    def get_default_merger(self) -> Merger:
        """
        Merge the account data into another DataFrame.
        This method is usually called by App when it merges all the accounts into a single DataFrame.

        The Account class implementing this method is resposible for performing any join or merge operation
        that is necessary to combine the account data with the other DataFrame.

        Args:
            other: DataFrame to merge the account data into.
        """
        return BoundMerger(self.merge_into, type(self), self, "Account.default_merger")

    def merge_into(self, ctx: MergeContext, df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge the account data into another DataFrame.
        This method is usually called by App when it merges all the accounts into a single DataFrame.

        The Account class implementing this method is resposible for performing any join or merge operation
        that is necessary to combine the account data with the other DataFrame.

        Args:
            ctx:   MergeContext object containing the accounts to merge.
            other: DataFrame to merge the account data into.
        """
        return pd.concat([df, self.data], ignore_index=True)

    ##############################################
    # Importer selection methods
    # only get_default_importer is required to be implemented.
    # Most accounts use the @with_locale_helper decorator automatically define those methods
    # if they follow the convention of managin the importers with monjour.utils.LocaleImporter
    ##############################################

    def get_default_importer(self, locale: str|None=None) -> Importer:
        """
        Get the importer to use for the account based on the locale.
        If no importer is defined and no locale is provided, an exception will be raised.
        """
        raise NotImplementedError()

    def set_importer(self, importer: Importer|str) -> Importer:
        """
        Sets the preferred importer for the account.
        The base implementation of Account can only set the importer if a full importer object is provided.
        To support selecting an importer by ID, the subclass should override this method.
        """
        if isinstance(importer, str):
            if self.importer.info.id == importer:
                return self.importer
            raise NotImplementedError()
        else:
            self._importer = importer
            return self._importer

    def get_available_importers(self) -> list[ImporterInfo]:
        """
        Enumerate the available importers for the account.
        This only return the ImporterInfo objects representing the available importers.
        To load the importer call set_importer with the ID of the importer (ImporterInfo.id)
        """
        return [self.importer.info]

    ##############################################
    # Importing (defers to the Importer)
    ##############################################

    def import_file(self, ctx: ImportContext) -> ImportContext:
        importer = self.importer
        # Import the file
        filepath = Path(ctx.filename)
        with open(filepath, 'rb') as f:
            df = importer.import_file(ctx, f)
            ctx.importer_id = importer.info.id
            ctx.result = df

        # Register with the archive that we are using an external file
        ctx.archive.register_file(self.id, ctx.importer_id, ctx.date_range, filepath)
        self.data = pd.concat([self.data, df])
        return ctx

    def archive_file(self, ctx: ImportContext, buffer: IO[bytes]) -> ImportContext:
        # Import the file
        importer = self.importer
        df = importer.import_file(ctx, buffer)
        ctx.importer_id = importer.info.id
        ctx.result = df

        # Save the file in the archive
        ext = ctx.filename.split('.')[-1]
        ctx.archive.archive_file(self.id, ctx.importer_id, ctx.date_range, buffer, ext)

        # Merge the new data into the account
        self.data = pd.concat([self.data, df])
        return ctx

    def load_from_archive(self, archive: Archive, archive_id: ArchiveID, check_hash=False):
        """
        Load a file from the archive into the account.

        Args:
            archive:    Archive object to use for loading the file.
            archive_id: ID of the file in the archive.
            check_hash: If True, the hash of the file will be checked before loading.
        """
        # Use the importer to read the file into a dataframe
        record = archive.get_record(archive_id)
        buf = archive.load_file(record['id'], check_hash=check_hash)
        import_context = ImportContext(self, archive, archive_id,
                    DateRange(record['date_start'], record['date_end']), record['file_path'])
        df = self.importer.import_file(import_context, buf)
        log.info(f"Loaded '{archive_id}' into account '{self.id}'")
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
            buf = archive.load_file(record['id'], check_hash=check_hash)
            import_context = ImportContext(self, archive, record['id'],
                    DateRange(record['date_start'], record['date_end']), record['file_path'])
            df = self.importer.import_file(import_context, buf)
            dfs.append(df)

        # Merge all the new data into the account
        self.data = pd.concat([self.data] + dfs)
