import pandas as pd
from abc import ABC, abstractmethod
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from monjour.core.account import Account

from monjour.core.archive import Archive, DateRange, ArchiveID

class ImporterInfo:
    id: str
    supported_locale: str
    version: str
    importer_class_name: str
    module: str
    friendly_name: str|None

    def __init__(self, locale: str, v: str, cls_name: str, module: str,
                 id: str|None=None, friendly_name: str | None = None):
        self.supported_locale = locale
        self.version = v
        self.importer_class_name = cls_name
        self.module = module
        self.friendly_name = friendly_name or f"{cls_name} {locale} v{v}"
        self.id = id or f'{cls_name}_{locale}_v{v}'

    def supports_locale(self, locale: str) -> bool:
        return self.supported_locale == '*' or self.supported_locale == locale

class InvalidFileError(Exception):
    pass

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
    info: ImporterInfo

    def __init__(self):
        super().__init__()

    @abstractmethod
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

def importer(locale: str, v: str, friendly_name: str | None = None):
    """
    Decorator for Importer classes.
    This decorator registers the decorated class as an Importer.

    Args:
        name:       Name of the importer.
        version:    Version of the importer.
        locale:     Locale supported by this importer. Use "*" to support all locales.
    """
    def decorator(cls):
        if not issubclass(cls, Importer):
            raise Exception('Only classes that inherit from Importer can be registered as Importers')
        def __init__(self: Importer):
            Importer.__init__(self)
        cls.__init__ = __init__
        cls.info = ImporterInfo(locale, v, cls.__name__, cls.__module__, friendly_name=friendly_name)
        return cls
    return decorator