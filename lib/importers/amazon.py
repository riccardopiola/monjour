"""
To download data from Amazon go to the following link:
https://www.amazon.com/hz/privacy-central/data-requests/preview.html
and select "Your Orders" in the dropdown menu
"""

import pandas as pd

from lib.framework import BalanceSheet, CONFIG
from lib.archive import DateRange, Archive, ImporterInfo, ArchiveRecord

class Amazon(BalanceSheet):

    def __init__(self, name: str = 'amazon'):
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