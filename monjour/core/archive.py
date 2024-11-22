import hashlib
import io
import datetime as dt
import json
from pathlib import Path
from typing import IO, TypeAlias, TypedDict, TYPE_CHECKING

import monjour.core.log as log
from monjour.core.common import DateRange
from monjour.core.constants import MONJOUR_VERSION

if TYPE_CHECKING:
    from monjour.core.importer import ImportContext

ArchiveID: TypeAlias = str

class HashMismatchError(Exception):
    pass

class ArchiveRecord(TypedDict):
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
    records: dict[str, ArchiveRecord]
    archiver_version: str

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
    """
    version = MONJOUR_VERSION

    # Still not sure records should be a dataframe instead of a dict
    records: dict[str, ArchiveRecord]
    archive_dir: Path
    archive_json_path: Path

    def __init__(self, archive_dir: Path|str):
        if isinstance(archive_dir, str):
            self.archive_dir = Path(archive_dir)
        else:
            self.archive_dir = archive_dir
        # Load the archive table from disk or create a new one if it doesn't exist
        self.archive_json_path = self.archive_dir / 'archive.json'
        self.records = {}

    @staticmethod
    def calculate_file_hash(buf: IO[bytes]) -> str:
        """
        Calculate the hash of the file contents.
        """
        buf.seek(0)
        return hashlib.md5(buf.read()).hexdigest()

    @staticmethod
    def calculate_archive_id(account_id: str, date_range: DateRange) -> ArchiveID:
        """
        Calculate the archive id for a file based on the account id and the date range.
        """
        return f'{account_id}_{date_range.start.strftime("%Y-%m-%d")}_{date_range.end.strftime("%Y-%m-%d")}'

    ########################################################
    # Convenience methods
    ########################################################

    def get_record(self, archive_id: ArchiveID) -> ArchiveRecord:
        """
        Get the record for the given archive id.
        """
        return self.records[archive_id]

    def ensure_hashes_match(self, archive_id: ArchiveID, hash: str):
        """
        Ensure the hash of the file matches the hash in the archive table.
        """
        if hash != self.records[archive_id]['file_hash']:
            raise HashMismatchError(f'File hash does not match for archive id {archive_id}')

    def get_records_for_account(self, account_id: str) -> list[ArchiveRecord]:
        return [record for record in self.records.values() if record['account_id'] == account_id]


    ########################################################
    # Archive record import
    ########################################################

    def register_file(
        self,
        account_id: str,
        importer_id: str,
        date_range: DateRange,
        filepath: Path,
    ) -> ArchiveID:
        """
        Register a file in the archive table without actually copying it to the archive directory.

        Args:
            account_id:         Name of the account that the file belongs to.
            importer_name:      Name of the importer that is importing the file.
            importer_version:   Version of the importer that is importing the file.
            date_range:         Date internal of transactions covered by the file.
            filepath:           Path to the file to register.

        Returns:
            Archive ID of the file.

        Raises:
            HashMismatchError: If the file has already been archived but the hash does not match.
        """
        with open(filepath, 'rb') as f:
            file_hash = Archive.calculate_file_hash(f)
        archive_id = self._register_file(account_id, importer_id, date_range, str(filepath), file_hash,
                                         is_managed_by_archive=False)
        return archive_id

    def archive_file(
        self,
        account_id: str,
        importer_id: str,
        date_range: DateRange,
        file: IO[bytes],
        extension: str, # Extension without the dot
    ) -> ArchiveID:
        """
        Archive a file in the archive directory and record the metadata in the archive table.

        Args:
            account_id:         Name of the account that the file belongs to.
            importer_name:      Name of the importer that is importing the file.
            importer_version:   Version of the importer that is importing the file.
            date_range:         Date internal of transactions covered by the file.
            file:               BytesIO object containing the file contents.
            extension:          Extension to use use for the file (not including dot).

        Returns:
            Archive ID of the file.

        Raises:
            HashMismatchError: If the file has already been archived but the hash does not match.
        """
        file_hash = Archive.calculate_file_hash(file)
        archive_id = Archive.calculate_archive_id(account_id, date_range)

        # Calculate the new filename
        archive_path = f"{account_id}/{archive_id}.{extension}"
        full_path = self.archive_dir / archive_path

        # Copy the file to the archive directory
        self._write(full_path, file)
        log.info(f"File '{archive_path}' copied to archive")

        # Note that we only pass filename to be saved in the 'file_path' field
        # The full path can be reconstructed by joining the archive_dir and the account_id
        archive_id = self._register_file(account_id, importer_id, date_range, archive_path, file_hash,
                                         is_managed_by_archive=True)
        return archive_id

    def _register_file(
        self,
        account_id: str,
        importer_id: str,
        date_range: DateRange,
        filepath: str,
        file_hash: str,
        is_managed_by_archive: bool,
    ):
        """
        Internal method to register a file in the archive table.
        If the file has already been archived, it will check the hash and raise an error if it doesn't match.
        """
        archive_id = Archive.calculate_archive_id(account_id, date_range)
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
        log.info(f"File '{filepath}' imported with id: {archive_id}")
        return archive_id

    def _reimport_file(
        self,
        archive_id: ArchiveID,
        importer_id: str,
        filepath: str,
        file_hash: str,
        is_managed_by_archive: bool,
    ) -> ArchiveID:
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
        log.info(f"File '{archive_id}' was re-imported")
        return archive_id

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
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            data.seek(0)
            f.write(data.read()) 

    def _read(self, src: Path) -> bytes:
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