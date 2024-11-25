import hashlib
import io
import datetime as dt
import json
import pandas as pd
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import IO, TypeAlias, TypedDict, TYPE_CHECKING

from monjour.core.log import MjLogger
from monjour.core.common import DateRange
from monjour.core.globals import MONJOUR_VERSION

if TYPE_CHECKING:
    from monjour.core.importer import ImportContext

ArchiveID: TypeAlias = str

log = MjLogger(__name__)

class HashMismatchError(Exception):
    pass

class ArchiveRecord(TypedDict):
    """
    Represents a file known to the archive. It can be:
    - A file that has been copied into the archive folder and now managed Archive
    - An external file (App.import)
    
    The discriminator is the 'is_managed_by_archive' field.
    """
    id: str
    imported_date: dt.datetime
    importer_id: str|None
    account_id: str
    file_path: str
    file_hash: str
    date_start: dt.datetime
    date_end: dt.datetime
    is_managed_by_archive: bool

class ArchiveInfo(TypedDict):
    """
    Persisted archive information. This object is serialized to disk in
    JSON format. Usually in $appdata_dir/archive/archive.json
    """
    records: dict[str, ArchiveRecord]
    archiver_version: str

class ArchiveOperationResult(Enum):
    Error = 0
    Registered = 1
    Archived = 2
    Reimported = 3

class Archive:
    """
    The Archive class is responsible for keeping track of the files that have been imported.

    When a file is imported, an Importer calls the archive_file method to copy the original file
    to the archive directory and record the metadata in the archive table.

    IMPORTANT: The files are archived before any preprocessing is done. This means that the files
    in the archive directory are the original files that were imported. The preprocessing is done on
    the fly when the file is loaded (by the importer).

    To get the file contents, an Importer calls the load_file method with the archive_id. The file is
    read from the archive directory and returned as bytes.

    The archive also keeps track of the metadata of the files that have been imported but are not in the
    archive directory.
    """
    version = MONJOUR_VERSION

    # Still not sure records should be a dataframe instead of a dict
    records: dict[str, ArchiveRecord]
    archive_dir: Path
    archive_json_path: Path
    _df: pd.DataFrame|None

    def __init__(self, archive_dir: Path|str):
        if isinstance(archive_dir, str):
            self.archive_dir = Path(archive_dir)
        else:
            self.archive_dir = archive_dir
        # Load the archive table from disk or create a new one if it doesn't exist
        self.archive_json_path = self.archive_dir / 'archive.json'
        self.records = {}
        self._df = None

    @staticmethod
    def calculate_file_hash(buf: IO[bytes]) -> str:
        """
        Calculate the hash of the file contents.
        """
        buf.seek(0)
        return hashlib.md5(buf.read()).hexdigest()

    @staticmethod
    def calculate_archive_id(account_id: str, file: IO[bytes]) -> ArchiveID:
        """
        Create a semi-deterministic archive id for the file based on the account id and the file hash.
        """
        hash = Archive.calculate_file_hash(file)
        return f"{account_id}_{hash}"

    ########################################################
    # Convenience methods
    ########################################################

    @property
    def df(self):
        """
        Return the archive table as a DataFrame. This is a cached property.
        """
        if self._df is None:
            self._df = pd.DataFrame.from_records(list(self.records.values()))
        return self._df

    def get_record(self, archive_id: ArchiveID) -> ArchiveRecord:
        """Get the record for the given archive id."""
        return self.records[archive_id]

    def ensure_hashes_match(self, archive_id: ArchiveID, hash: str):
        """Ensure the hash of the file matches the hash in the archive table."""
        if hash != self.records[archive_id]['file_hash']:
            raise HashMismatchError(f'File hash does not match for archive id {archive_id}')

    def get_records_for_account(self, account_id: str) -> list[ArchiveRecord]:
        """Get all records for the given account id."""
        return [record for record in self.records.values() if record['account_id'] == account_id]


    ########################################################
    # Archive record import
    ########################################################

    def archive_file(
        self,
        archive_id: ArchiveID,
        account_id: str,
        importer_id: str,
        date_range: DateRange,
        file: IO[bytes],
        extension: str, # Extension without the dot
    ) -> ArchiveOperationResult:
        """
        Archive a file in the archive directory and record the metadata in the archive table.

        Args:
            archive_id:         ID of the file to archive (previously obtained with calculate_archive_id).
            account_id:         Name of the account that the file belongs to.
            importer_id:        ID of the importer that has parsed the file.
            date_range:         Date internal of transactions covered by the file.
            file:               BytesIO object containing the file contents.
            extension:          Extension to use use for the file (not including dot).

        Returns:
            ArchiveOperationResult: The result of the operation. (Archived, Reimported)

        Raises:
            HashMismatchError: If the file has already been archived but the hash does not match.
        """
        # Calculate the new filename
        archive_path = f"{account_id}/{archive_id}.{extension}"
        full_path = self.archive_dir / archive_path

        # Note that we only pass filename to be saved in the 'file_path' field
        # The full path can be reconstructed by joining the archive_dir and the account_id
        result = self.register_file(archive_id, account_id, importer_id, date_range, archive_path,
                                         is_managed_by_archive=True)
        if not result == ArchiveOperationResult.Registered:
            return result

        # Copy the file to the archive directory
        self._write(full_path, file)
        log.info(f"File copied (archive_id: {archive_id}) (path: {archive_path})")

        return ArchiveOperationResult.Archived

    def register_file(
        self,
        archive_id: ArchiveID,
        account_id: str,
        importer_id: str,
        date_range: DateRange,
        filepath: str,
        is_managed_by_archive: bool = False,
    ) -> ArchiveOperationResult:
        """
        Register a file in the archive table.

        Args:
            archive_id:         ID of the file to archive (previously obtained with calculate_archive_id).
            account_id:         Name of the account that the file belongs to.
            importer_id:        ID of the importer that has parsed the file.
            date_range:         Date internal of transactions covered by the file.
            filepath:           Path to the file. If the file is managed by the archive, this should be the filename.
            is_managed_by_archive: If True, the file is managed by the archive and is stored in the archive directory.

        Returns:
            ArchiveOperationResult: The result of the operation. (Registered, Reimported)

        Raises:
            HashMismatchError: If the file has already been archived but the hash does not match.
        """
        file_hash = archive_id[len(account_id):]
        if archive_id in self.records:
            record = self.records[archive_id]
            if file_hash == record['file_hash']:
                return self._reimport_file(archive_id, importer_id, filepath, file_hash, is_managed_by_archive)
            else:
                raise HashMismatchError(f'File {archive_id} has already been archived but the hash does not match')

        # Add record to the records table
        self.records[archive_id] = ArchiveRecord(
            id                = archive_id,
            imported_date     = dt.datetime.now(),
            importer_id       = importer_id,
            account_id        = account_id,
            file_path         = filepath,
            file_hash         = file_hash,
            date_start        = date_range.start,
            date_end          = date_range.end,
            is_managed_by_archive= is_managed_by_archive,
        )
        self.save()
        log.info(f"File registered (archive_id: {archive_id}) (path: {filepath})")
        return ArchiveOperationResult.Registered

    def _reimport_file(
        self,
        archive_id: ArchiveID,
        importer_id: str,
        filepath: str,
        file_hash: str,
        is_managed_by_archive: bool,
    ) -> ArchiveOperationResult:
        """
        A file with the same archive id has already been imported. Check if the new file is the same.
        """
        # Right now the archive is very strict and doesn't allow re-importing files with different hashes
        # We might want to relax this in the future
        prev = self.records[archive_id]
        if prev['is_managed_by_archive'] != is_managed_by_archive:
            raise ValueError(f'Cannot re-import file {archive_id} with different management status')
        if prev['file_hash'] != file_hash:
            raise ValueError(f'Cannot re-import file {archive_id} with different hash')
        if prev['importer_id'] != importer_id:
            log.warning(f'File {archive_id} was imported with a different importer ({prev['importer_id']}). The record has been updated to the new importer.')
            prev['importer_id'] = importer_id
        prev['imported_date'] = dt.datetime.now()
        prev['file_path'] = filepath

        self.save()
        log.info(f"File reimported (archive_id: {archive_id}) (path: {filepath})")
        return ArchiveOperationResult.Reimported

    ########################################################
    # Archive records management
    ########################################################

    def load_file(self, archive_id: ArchiveID, check_hash: bool) -> io.BytesIO:
        """
        Load the file with the given archive id from the archive directory.

        Args:
            archive_id: ID of the file to load.
            check_hash: If True, the hash of the file will be checked before loading.

        Returns:
            BytesIO object containing the file contents.

        Raises:
            FileNotFoundError: If the file is not found in the archive directory.
            HashMismatchError: If the hash of the file does not match the hash in the archive table.
        """
        record = self.records[archive_id]

        # Read file from disk
        if record['is_managed_by_archive']:
            # Records managed by the archive only save the file name in the 'file_path' field
            file_path = self.archive_dir / record['file_path']
        else:
            # Extenral records save the full path in the 'file_path' field
            file_path = Path(record['file_path'])
        file_contents = self._read(file_path)

        if check_hash:
            file_hash = hashlib.md5(file_contents).hexdigest()
            if file_hash != record['file_hash']:
                raise HashMismatchError(f'File hash does not match for archive id {archive_id}')
        self._df = None
        return io.BytesIO(file_contents)

    def forget_file(self, archive_id: ArchiveID):
        """
        Remove the file from the archive directory and the metadata from the archive table.
        """
        record = self.records[archive_id]
        file_path: Path = Path(self.config.archive_dir) / record['account_id'] / record['file_name'] # type: ignore
        file_path.unlink()
        self.records.pop(archive_id)
        log.info(f"Forgotten file '{archive_id}'")

    ########################################################
    # Implementation of filesystem I/O
    ########################################################

    def _write(self, dest: Path, data: IO[bytes]):
        """Implementation of a filesystem write operation."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            data.seek(0)
            f.write(data.read()) 

    def _read(self, src: Path) -> bytes:
        """Implementation of a filesystem read operation."""
        return src.read_bytes()

    ########################################################
    # Archive metadata management
    ########################################################

    def save(self, filepath: Path|None=None):
        """
        Save the archive state to disk.
        """
        # Custom serializer function
        def custom_serializer(obj):
            if isinstance(obj, dt.datetime):
                return obj.isoformat()  # Convert datetime to string
            raise TypeError(f"Type {type(obj)} not serializable")

        path = filepath or self.archive_json_path
        archive_info: ArchiveInfo = {
            'records': self.records,
            'archiver_version': self.version
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        json_str = json.dumps(archive_info, default=custom_serializer, indent=4)
        self._write(path, io.BytesIO(json_str.encode()))

    def load(self, filepath: Path|None=None):
        """
        Load the archive state from disk.
        """
        path = filepath or self.archive_json_path
        if not path.exists():
            return
        buf = self._read(path)
        archive_info: ArchiveInfo = json.loads(buf)
        if archive_info['archiver_version'] != self.version:
            raise Exception(f'Archive version mismatch. Expected {self.version}, got {archive_info["archiver_version"]}')
        # Invidivual records need some processing
        for record in archive_info['records'].values():
            record['imported_date'] = dt.datetime.fromisoformat(record['imported_date']) # type: ignore
            record['date_start']    = dt.datetime.fromisoformat(record['date_start']) # type: ignore
            record['date_end']      = dt.datetime.fromisoformat(record['date_end']) # type: ignore
        self.records = archive_info['records']


class InMemoryArchive(Archive):
    """
    An in-memory archive mostly for testing and debugging.
    This archive should behave exactly like a regular archive but it doesn't write to disk.
    """
    fs: dict[str, bytes]

    def __init__(self, archive_dir: Path|str):
        super().__init__(archive_dir)
        self.fs = {}

    def _write(self, dest: Path, data: IO[bytes]):
        self.fs[str(dest)] = data.read()

    def _read(self, src: Path) -> bytes:
        return self.fs[str(src)]

class WriteOnlyArchive(Archive):
    """
    An archive that doesn't read files from disk. Useful only for testing and debugging.
    """
    def _read(self, src: Path) -> bytes:
        raise NotImplementedError('WriteOnlyArchive does not support reading files')

    def _write(self, dest: Path, data: IO[bytes]):
        pass