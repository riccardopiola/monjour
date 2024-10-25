import pandas as pd
import datetime

from lib.framework import BalanceSheet, CONFIG
from lib.archive import DateRange, Archive, ImporterInfo, ArchiveRecord

PAYPAL_IMPORTER = ImporterInfo('Paypal', '0.1')

class Paypal(BalanceSheet):

    def __init__(self, name: str = 'paypal'):
        super().__init__(name)

    def initialize(self, archive: Archive):
        # Load all the files from the archive into the in-memory balance sheet
        for id, record in archive.records[archive.records['sheet_name'] == self.id].iterrows():
            with archive.load_file(id) as file: # type: ignore
                pass

    def merge_into(self, other: pd.DataFrame):
        # Merge the data from this balance sheet into another one
        other = pd.concat([other, self.data], ignore_index=True)
        return other
