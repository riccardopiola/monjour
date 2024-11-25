from typing import IO, ClassVar, Self
import pandas as pd

from monjour.core.log import MjLogger
from monjour.core.archive import Archive, ArchiveID
from monjour.core.common import DateRange
from monjour.core.config import Config
from monjour.core.importer import ImportContext, Importer, ImporterInfo
from monjour.core.merge import MergeContext, Merger, BoundMerger
from monjour.core.transaction import Transaction

log = MjLogger(__name__)

class Account:
    """
    Base class representing any list of transactions.
    It is a thin wrapper around a DataFrame that also contains additional logic for:
    - Importing new files (or deferring the import to an Importer object)
    - Merging the data into a master DataFrame.

    NOTE: initialize() is separated from __init__ to allow the account to be create without a Config object.
    Account objects should not be used before initialize() is called.

    Class Attributes:
        PROVIDER_ID:    Unique identifier for the provider of the account.
        TRANSACTION_TYPE: Type of transactions that the account contains.
        COLUMN_ORDER:   Alternative order for the columns in the DataFrame (for display purpoises).

    Attributes:
        id:         Unique identifier for the account.
        data:       DataFrame containing the transactions.
        name:       Optional readable name for the account.
        locale:     Optional locale for the account. (Used to auto select the right importer)
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

    @property
    def importer(self) -> Importer:
        """
        Loads the importer class to use to import new files into the account.
        If no importer is defined, the default importer will be loaded based on the locale.
        If an importer was set in __init__, or with set_importer, it will be used instead.
        """
        if self._importer is None:
            self._importer = self.get_default_importer(self.locale)
        return self._importer

    @property
    def merger(self) -> Merger:
        """
        Get a merger cabable of merging the account data into another DataFrame.
        For more information about Mergers, see the monjour.core.merge module.
        - The returned merger will be the one specified in `__init__` or the default merger if none was provided.
        - Derived classes should not override this method, but instead override `get_default_merger` or `merge_into`.
        """
        if self._merger is None:
            self._merger = self.get_default_merger()
        return self._merger

    ##############################################
    # Merge methods
    ##############################################

    def get_default_merger(self) -> Merger:
        """
        Get the default merge for this account. This base implementation returns
        a merger that forwards the call to the merge_into method of the account.
        Derived classes can either override this method to provide a custom Merger
        object or more simply override the merge_into method to provide the merging logic.
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

    def merge_fragment(self, ctx: ImportContext, df: pd.DataFrame):
        """
        Method called after an importer has imported a file to merge the new data into the account.

        An account is often the aggregation of multiple files. For example, a bank account can have
        multiple CSV files relating to different months/years stored separetely in the archive.
        These records are loaded into the account one by one and merged into the account's DataFrame.

        Args:
            ctx: ImportContext object containing the context of the import operation.
            df:  DataFrame containing the transactions imported from the file.
        """
        self.data = pd.concat([self.data, df])

    ##############################################
    # Importer selection methods
    # only get_default_importer is required to be implemented.
    # Most accounts use the @with_locale_helper decorator (see monjour.utils.locale_importer)
    # to automatically define the importer selection methods below. 
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
        """
        Imports a file from the local filesystem into this account. This function:
        - Parses the file with the importer
        - Adds a record to ther archive recording the import
        - Merges the new data into the account's DataFrame

        It DOES NOT copy the file into the archive folder. Use archive_file for that.
        """
        importer = self.importer
        # Import the file
        with open(ctx.filename, 'rb') as f:
            df = importer.import_file(ctx, f)
            ctx.importer_id = importer.info.id
            ctx.result = df

        # Register with the archive that we are using an external file
        ctx.archive_operation_result = ctx.archive.register_file(ctx.archive_id, self.id,
                                            ctx.importer_id, ctx.date_range, ctx.filename)
        self.merge_fragment(ctx, df)
        return ctx

    def archive_file(self, ctx: ImportContext, buffer: IO[bytes]) -> ImportContext:
        """
        Imports a file from a buffer into this account. This function:
        - Parses the file with the importer
        - COPIES the file into the archive folder
        - Adds a record to ther archive recording the import
        - Merges the new data into the account's DataFrame
        """
        # Import the file
        importer = self.importer
        buffer.seek(0)
        df = importer.import_file(ctx, buffer)
        ctx.importer_id = importer.info.id
        ctx.result = df

        # Save the file in the archive
        ext = ctx.filename.split('.')[-1]
        ctx.archive_operation_result = ctx.archive.archive_file(ctx.archive_id, self.id,
                                            ctx.importer_id, ctx.date_range, buffer, ext)

        # Merge the new data into the account
        self.merge_fragment(ctx, df)
        return ctx

    def load_all_from_archive(self, archive: Archive):
        """
        Load all files previously saved in the archive into the account.
        """
        archive_records = archive.get_records_for_account(self.id)
        for record in archive_records:
            self.load_from_archive(archive, record['id'])

    def load_from_archive(self, archive: Archive, archive_id: ArchiveID):
        """
        Load a single file from the archive into the account.

        Args:
            archive:    Archive object to use for loading the file.
            archive_id: ID of the file in the archive.
        """
        # Use the importer to read the file into a dataframe
        record = archive.get_record(archive_id)
        buf = archive.load_file(record['id'])
        importer = self.importer
        ctx = ImportContext(self, archive, archive_id, DateRange(record['date_start'], record['date_end']),
                            record['file_path'], importer_id=importer.info.id)
        df = importer.import_file(ctx, buf)
        log.info(f"Loaded archived file {archive_id} into account '{self.id}'")
        # Merge the new data into the account
        self.merge_fragment(ctx, df)

    def copy(self) -> Self:
        """
        Return a new Account object containing the same data as this account.
        - The configuration is copied by reference, as it should be immutable.
        - Any data is copied by value

        Derived classes that have different init methods should override this.
        """
        other = type(self)(self.id, self.name, self.locale, self._importer, self._merger)
        other.initialize(self.config)
        other.data = self.data.copy()
        return other
