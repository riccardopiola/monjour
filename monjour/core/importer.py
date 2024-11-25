import copy
import pandas as pd
from abc import ABC, abstractmethod
from typing import IO, TYPE_CHECKING

from monjour.core.executor import Executor
from monjour.core.archive import Archive, DateRange, ArchiveID, ArchiveOperationResult
from monjour.utils.diagnostics import DiagnosticCollector, Diagnostic

if TYPE_CHECKING:
    from monjour.core.account import Account

DEFAULT_IMPORT_EXECUTOR = Executor["ImportContext", pd.DataFrame]()

class ImportContext(DiagnosticCollector):
    """
    Context object that is passed to the various classes partecipating in the import process.
    This object contains all the information an Importer might need to import a file.

    - The context is mostly? immutable, with the exception of the result and 'extra' fields. (should probably be immutable)
    - The context collects diagnostics that are generated during the import process.
    - The context doubles as the object representing the result of the an import operation.

    Attributes:
        account:    Account object that the file is being imported for.
        archive:    Archive object that will be used to store the file.
        archive_id: ID of the archive that will be used to store the file.
        date_range: Date range associated with the file.
        filename:   Name of the file being imported.
        importer_id:    ID of the importer that will be used to import the file.
        executor:   Executor that will be used to execute the import process.
        extra:      Extra information that can be passed to the importer or within the importer.
        result:     Result of the import process. This field is set at the end of the import process.
    """
    account: "Account"
    archive: Archive
    archive_id: ArchiveID
    date_range: DateRange
    filename: str
    importer_id: str

    executor: Executor["ImportContext", pd.DataFrame] = DEFAULT_IMPORT_EXECUTOR
    extra: dict

    result: pd.DataFrame|None = None
    archive_operation_result: ArchiveOperationResult|None = None

    def __init__(self, account: "Account", archive: Archive, archive_id: ArchiveID,
                 date_range: DateRange, filename: str, importer_id: str,
                 executor: Executor["ImportContext", pd.DataFrame]=DEFAULT_IMPORT_EXECUTOR,
                 extra: dict|None=None):
        super().__init__(f"ImportContext({account.id}, {importer_id})")
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
    """
    Infomation about an Importer. Decorate an importer with @importer to fill in this information.

    Importers are not loaded until they are needed, so this class is used to store information
    about an importer and its capabilities without actually loading the importer.

    Attributes:
        id:                     Unique ID of the importer.
        supported_locale:       Locale supported by this importer. Use "*" to support all locales.
        version:                Version of the importer.
        importer_class_name:    Name of the importer class.
        module:                 Module where the importer class is defined.
        friendly_name:          Friendly name of the importer.
        supports_executor:      Whether the importer supports the use of an executor. (not used at the moment)
    """
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
    Abstract base class for all Importers. Importers take in a file (usually a CSV file
    but it can be any file) and parse it into a DataFrame.
    The importer's capabilities are defined by the ImporterInfo object.
    """
    info: ImporterInfo

    def __init__(self):
        super().__init__()

    @abstractmethod
    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame:
        """Import a file into a DataFrame."""
        ...

    def try_infer_daterange(
        self,
        file: IO[bytes],
        filename: str|None=None,
    ) -> DateRange:
        """
        The importer will try to infer the date range of the file from the filename or, if not possible,
        by loading the file itself.
        """
        raise NotImplementedError("This importer doesn't support inferring the date range automatically")

def importer(locale: str, v: str, friendly_name: str | None = None, supports_executor: bool = False):
    """
    Decorator for Importer classes.

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