import copy
import pandas as pd
from abc import ABC, abstractmethod
from typing import IO, TYPE_CHECKING

from monjour.utils.diagnostics import DiagnosticCollector
from monjour.core.executor import Executor

if TYPE_CHECKING:
    from monjour.core.account import Account

from monjour.core.archive import Archive, DateRange, ArchiveID

DEFAULT_IMPORT_EXECUTOR = Executor["ImportContext", pd.DataFrame]()

class ImportContext(DiagnosticCollector):
    account: "Account"
    archive: Archive
    archive_id: ArchiveID
    date_range: DateRange
    filename: str
    importer_id: str|None = None

    executor: Executor["ImportContext", pd.DataFrame] = DEFAULT_IMPORT_EXECUTOR
    extra: dict
    result: pd.DataFrame|None = None

    def __init__(self, account: "Account", archive: Archive, archive_id: ArchiveID,
                 date_range: DateRange, filename: str, importer_id: str|None=None,
                 executor: Executor["ImportContext", pd.DataFrame]=DEFAULT_IMPORT_EXECUTOR,
                 extra: dict|None=None):
        super().__init__()
        self.account = account
        self.archive = archive
        self.archive_id = archive_id
        self.date_range = date_range
        if "." not in filename:
            raise ValueError(f"Filename '{filename}' doesn't have an extension")
        self.filename = filename
        self.importer_id = importer_id
        self.executor = executor
        self.extra = extra or dict()

    def copy(self):
        """
        Performs a shallow copy the immutable fields and a deep copy of the mutable fields
        for the benefit of DebugExecutor.
        """
        return ImportContext(
            self.account,
            self.archive,
            self.archive_id,
            self.date_range,
            self.filename,
            self.importer_id,
            self.executor,
            copy.deepcopy(self.extra),
        )

class ImporterInfo:
    id: str
    supported_locale: str
    version: str
    importer_class_name: str
    module: str
    friendly_name: str|None
    supports_executor: bool

    def __init__(self, locale: str, v: str, cls_name: str, module: str, id: str|None=None,
                 friendly_name: str | None = None, supports_executor: bool = False):
        self.supported_locale = locale
        self.version = v
        self.importer_class_name = cls_name
        self.module = module
        self.friendly_name = friendly_name or f"{cls_name} {locale} v{v}"
        self.id = id or f'{cls_name}_{locale}_v{v}'
        self.supports_executor = supports_executor

    def supports_locale(self, locale: str) -> bool:
        return self.supported_locale == '*' or self.supported_locale == locale

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
    info: ImporterInfo

    def __init__(self):
        super().__init__()

    @abstractmethod
    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame|None:
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
    ) -> pd.DataFrame|None:
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

    def try_infer_daterange(
        self,
        file: IO[bytes],
        filename: str|None=None,
    ) -> DateRange:
        raise NotImplementedError()

def importer(locale: str, v: str, friendly_name: str | None = None, supports_executor: bool = False):
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
        def __init__(self):
            super(cls, self).__init__()
        cls.__init__ = __init__
        cls.info = ImporterInfo(locale, v, cls.__name__, cls.__module__,
                                friendly_name=friendly_name, supports_executor=supports_executor)
        return cls
    return decorator