import pandas as pd
from abc import ABC, abstractmethod
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from monjour.core.account import Account

from monjour.core.archive import Archive, DateRange, ArchiveID

class ImportContext:
    account: "Account"
    archive: Archive
    archive_id: ArchiveID
    date_range: DateRange
    extra: dict

    def __init__(self, account: "Account", archive: Archive, archive_id: ArchiveID,
                 date_range: DateRange,extra: dict = {}):
        self.account = account
        self.archive = archive
        self.archive_id = archive_id
        self.date_range = date_range
        self.extra = extra

class InvalidFileError(Exception):
    pass

class Importer(ABC):
    """
    Base class for all Importers.

    When a new file is imported, the Importer is responsible for archiving the file and
    loading it into a DataFrame.

    Usually the Importer and the Account are separate classes. This way the same account can
    have multiple importers, each one responsible for a different type of file or different locale.
    For simple cases, the Importer can be the same as the Account.
    """

    # To be defined by concrete classes
    name: str
    version: str

    account: "Account"

    def __init__(self, account: "Account"):
        super().__init__()
        self.account = account

    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame:
        """
        Archive a new file using the provided archiver and return the archive_id.
        This call doesn't require the file to be parsed into a DataFrame.

        Args:
            archive:    Archive to use to store the file.
            file:       Path or buffer to the file to import.
            date_range: Optional date range to associate with the file.
        """
        ...

    def try_import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame:
        """
        Try to import a file and return the archive_id if successful.
        If the file cannot be imported, return None.

        Args:
            file:       Path or buffer to the file to import.
            date_range: Optional date range to associate with the file.

        Returns:
            ArchiveID of the imported file if successful,

        Raises:
            InvalidFileError: If the file cannot be imported.
            NotImplementedError: If the importer doesn't support this operation.
        """
        raise NotImplementedError()

def importer(name: str, version: str):
    """
    Decorator for Importer classes.
    This decorator registers the decorated class as an Importer.
    """
    def decorator(cls):
        if not issubclass(cls, Importer):
            raise Exception('Only classes that inherit from Importer can be registered as Importers')
        def __init__(self: Importer, account: "Account"):
            Importer.__init__(self, account)
        cls.__init__ = __init__
        cls.name = name
        cls.version = version
        return cls
    return decorator