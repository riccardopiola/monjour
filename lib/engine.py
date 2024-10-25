import pandas as pd

from lib.framework import BalanceSheet, Category, Config
from lib.archive import Archive, DateRange

class Engine:
    config: Config
    sheets: dict[str, BalanceSheet]
    categories: dict[str, Category]
    archive: Archive
    df: pd.DataFrame

    def __init__(self):
        from lib.framework import CONFIG, IMPORTERS, CATEGORIES
        self.config = CONFIG
        self.sheets = {}
        self.categories = {}
        for sheet in IMPORTERS:
            self.sheets[sheet.id] = sheet
        for category in CATEGORIES:
            self.categories[category.name] = category
        self.archive = Archive(self.config)
        self.df = pd.DataFrame()

        for sheet in self.sheets.values():
            sheet.initialize(self.archive)

    def import_new(self, sheet_id: str, file: str,
                   date_range: DateRange|None = None):

        self.sheets[sheet_id].import_new_file(self.archive, file, date_range)

    def create_master_sheet(self, include: list[str] = [], exclude: list[str] = []):
        """
        Create a master sheet by combining all the sheets in the include list
        """
        self.df = pd.DataFrame() # Reset the master sheet
        sheets_to_include = set(include if len(include) > 0 else self.sheets.keys()) - set(exclude)

        for sheet in self.sheets.values():
            # Filter out sheets that are not in the include list
            if sheet.id not in sheets_to_include:
                continue
            # Remove sheet from the include list
            sheets_to_include.remove(sheet.id)
            # Append the data to the master sheet
            self.df = pd.concat([self.df, sheet.data], axis=0)

        if len(sheets_to_include) > 0:
            raise Exception(f'Cannot include sheets: {sheets_to_include}')

