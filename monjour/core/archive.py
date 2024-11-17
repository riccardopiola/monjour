import hashlib
import io
import datetime as dt
import json
from pathlib import Path
from typing import IO, TypeAlias, TypedDict, TYPE_CHECKING

import monjour.core.log as log
from monjour.core.common import DateRange

if TYPE_CHECKING:
    from monjour.core.config import Config

ArchiveID: TypeAlias = str

class HashMismatchError(Exception):
    pass

class ArchiveRecord(TypedDict):
    id: str
    imported_date: dt.datetime
    importer_name: str
    importer_version: str
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
    version = '1.0'

    # Still not sure records should be a dataframe instead of a dict
    records: dict[str, ArchiveRecord]
    config: "Config"
    archive_file_path: Path

    def __init__(self, config: "Config"):
        self.config = config

        # Load the archive table from disk or create a new one if it doesn't exist
        self.archive_file_path = Path(config.archive_dir) / 'archive.json'
        if not self.archive_file_path.exists():
            self.records = {}
            self.save()
        else:
            self.load()

    @staticmethod
    def calculate_archive_id(account_id: str, date_range: DateRange) -> ArchiveID:
        """
        Calculate the archive id for a file based on the account id and the date range.
        """
        return f'{account_id}_{date_range.start.strftime("%Y-%m-%d")}_{date_range.end.strftime("%Y-%m-%d")}'

    @staticmethod
    def calculate_file_hash(buf: IO[bytes]) -> str:
        """
        Calculate the hash of the file contents.
        """
        return hashlib.md5(buf.read()).hexdigest()

    ########################################################
    # Convenience methods
    ########################################################

    def is_archive_id_free(self, archive_id: ArchiveID) -> bool:
        """
        Check if the archive id is not already in use.
        """
        return archive_id not in self.records

    def get_record(self, archive_id: ArchiveID) -> ArchiveRecord:
        """
        Get the record for the given archive id.
        """
        return self.records[archive_id]

    def get_file_path(self, archive_id: ArchiveID) -> Path:
        record = self.records[archive_id]
        folder_path: Path = Path(self.config.archive_dir) / record['account_id'] # type: ignore
        return folder_path / record['file_name'] # type: ignore

    def ensure_hashes_match(self, archive_id: ArchiveID, hash: str):
        """
        Ensure the hash of the file matches the hash in the archive table.
        """
        if hash != self.records[archive_id]['file_hash']:
            raise HashMismatchError(f'File hash does not match for archive id {archive_id}')

    def get_date_range(self, archive_id: ArchiveID) -> DateRange:
        record = self.records[archive_id]
        return DateRange(record['date_start'], record['date_end']) # type: ignore

    def get_records_for_account(self, account_id: str) -> list[ArchiveRecord]:
        return [record for record in self.records.values() if record['account_id'] == account_id]


    ########################################################
    # Archive record import
    ########################################################

    def register_file(
        self,
        account_id: str,
        importer_name: str,
        importer_version: str,
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
        archive_id = self._register_file(account_id, importer_name, importer_version, date_range,
                                         str(filepath), file_hash, is_managed_by_archive=False)
        return archive_id

    def archive_file(
        self,
        account_id: str,
        importer_name: str,
        importer_version: str,
        date_range: DateRange,
        file: IO[bytes],
        extension: str,
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

        # Calculate the new filename
        archive_id = Archive.calculate_archive_id(account_id, date_range)
        filename = archive_id + extension
        filepath = Path(self.config.archive_dir) / account_id / filename

        # Copy the file to the archive directory
        with open(filepath, 'wb') as fin:
            with open(filepath, 'rb') as fout:
                fin.write(fout.read())

        # Note that we only pass filename to be saved in the 'file_path' field
        # The full path can be reconstructed by joining the archive_dir and the account_id
        archive_id = self._register_file(account_id, importer_name, importer_version, date_range,
                                            filename, file_hash, is_managed_by_archive=True)
        return archive_id

    def _register_file(
        self,
        account_id: str,
        importer_name: str,
        importer_version: str,
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
            if file_hash == self.records[archive_id]['file_hash']:
                log.info(f'File {archive_id} has already been archived')
                return archive_id
            else:
                raise HashMismatchError(f'File {archive_id} has already been archived but the hash does not match')

        # Add record to the records table
        self.records[archive_id] = ArchiveRecord(
            id                = archive_id,
            imported_date     = dt.datetime.now(),
            importer_name     = importer_name,
            importer_version  = importer_version,
            account_id        = account_id,
            file_path         = filepath,
            file_hash         = file_hash,
            date_start        = date_range.start,
            date_end          = date_range.end,
            is_managed_by_archive= is_managed_by_archive,
        )
        self.save()
        log.info(f'Imported file {filepath} for account {account_id}')
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
            file_path = Path(self.config.archive_dir) / record['account_id'] / record['file_path']
        else:
            # Extenral records save the full path in the 'file_path' field
            file_path = Path(record['file_path'])
        if not file_path.exists():
            raise FileNotFoundError(f'File {file_path} not found in archive')
        file_contents = file_path.read_bytes()

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
        log.info(f'Forgotten file {archive_id}')

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

        path = filepath or self.archive_file_path
        archive_info: ArchiveInfo = {
            'records': self.records,
            'archiver_version': self.version
        }
        with open(path, 'w') as f:
            json.dump(archive_info, f, default=custom_serializer, indent=4)

    def load(self, filepath: Path|None=None):
        """
        Load the archive state from disk.
        """
        path = filepath or self.archive_file_path
        with open(path, 'r') as f:
            archive_info: ArchiveInfo = json.load(f)
            if archive_info['archiver_version'] != self.version:
                raise Exception(f'Archive version mismatch. Expected {self.version}, got {archive_info["archiver_version"]}')
            # Invidivual records need some processing
            for record in archive_info['records'].values():
                record['imported_date'] = dt.datetime.fromisoformat(record['imported_date']) # type: ignore
                record['date_start']    = dt.datetime.fromisoformat(record['date_start']) # type: ignore
                record['date_end']      = dt.datetime.fromisoformat(record['date_end']) # type: ignore
            self.records = archive_info['records']
