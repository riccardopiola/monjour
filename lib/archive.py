from pathlib import Path
from typing import Any, TypedDict, TYPE_CHECKING
import pandas as pd
import uuid
import hashlib
from datetime import datetime
from dataclasses import dataclass

import lib.log as log

if TYPE_CHECKING:
    from lib.framework import Config

@dataclass
class ImporterInfo:
    name: str
    version: str

@dataclass
class DateRange:
    start: datetime|None
    end: datetime

class ArchiveRecord(TypedDict):
    id: str
    imported_date: datetime
    importer_name: str
    importer_version: str
    sheet_name: str
    file_name: str
    file_hash: str
    date_start: datetime|None
    date_end: datetime


class Archive:
    records: pd.DataFrame
    config: "Config"

    def __init__(self, config: "Config"):
        self.records = pd.DataFrame({
            'id': [],
            'imported_date': [],
            'importer_name': [],
            'importer_version': [],
            'sheet_name': [],
            'file_name': [],
            'file_hash': [],
            'date_start': [],
            'date_end': [],
        })
        self.config = config
        self.records.set_index('id', inplace=True)

    def archive_file(
            self,
            sheet_name: str,
            filepath: str,
            importer_info: ImporterInfo,
            date_range: DateRange
        ) -> str:
        # Calculate file hash
        with open(filepath, 'rb') as file:
            file_contents = file.read()
            file_hash = hashlib.md5(file_contents).hexdigest()

        # Generate unique file id
        while (file_id := str(uuid.uuid4())) in self.records.index:
            continue

        # Calculate filename
        if date_range.start is None:
            filename = f'{sheet_name}_{date_range.end.strftime("%Y-%m-%d")}.csv'
        else:
            filename = f'{sheet_name}_{date_range.start.strftime("%Y-%m-%d")}_{date_range.end.strftime("%Y-%m-%d")}.csv'

        # Add record to the records table
        self.records.loc[file_id] = { # type: ignore
            'id'               : file_id,
            'imported_date'    : datetime.now(),
            'importer_name'    : importer_info.name,
            'importer_version' : importer_info.version,
            'sheet_name'       : sheet_name,
            'file_name'        : filename,
            'file_hash'        : file_hash,
            'date_start'       : date_range.start,
            'date_end'         : date_range.end,
        }

        # Save file to disk
        folder_path = Path(self.config.archive_dir) / sheet_name
        folder_path.mkdir(parents=True, exist_ok=True)
        file = folder_path / filename
        file.write_bytes(file_contents)

        log.info(f'Archived file {filename} for sheet {sheet_name}')

        return file_id # Return the file id

    def load_file(self, archive_id: str):
        record = self.records[archive_id]
        folder_path = Path(self.config.archive_dir) / record['sheet_name']
        file = folder_path / record['file_name']
        return open(file, 'r')