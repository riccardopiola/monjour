from typing import Callable, Self
import pandas as pd
from enum import Enum

from lib.framework import BankingSheet
from lib.archive import DateRange, Archive, ImporterInfo, ArchiveRecord

UNICREDIT_IMPORTER = ImporterInfo('Unicredit', '0.1')

class UnicreditCategory(Enum):
    UNKNOWN             = 'Unknown'             # 'Original: N/A'
    # Fees
    INTEREST_FEES       = 'Interest/Fees'       # 'COMPETENZE (INTERESSI/ONERI)'
    COMMISSIONS_FEES    = 'Commissions/Fees'    # 'COMMISSIONI - PROVVIGIONI - SPESE'
    FIXED_MONTHLY_COST  = 'Fixed Monthly Cost'  # 'MY GENIUS COSTO FISSO MESE'
    TAXES               = 'Taxes'               # 'IMPOSTA BOLLO CONTO CORRENTE DPR642/72-DM24/5/2012'

    # Payments
    PAYMENT             = 'Payment'             # 'PAGAMENTO' or 'PAGAMENTO GOOGLE PAY NFC'
    OTHER_PAYMENTS      = 'Other Payments'      # 'PAGAMENTI DIVERSI'
    OUTGOING_TRANSFER   = 'Outgoing Transfer'   # 'DISPOSIZIONE DI BONIFICO'
    SEPA_DIRECT_DEBIT   = 'SEPA Direct Debit'   # 'ADDEBITO SEPA DD PER FATTURA A VOSTRO CARICO'
    ECOMMERCE           = 'ECommerce'           # 'PAGAMENTO E-Commerce' or 'PAGAMENTO GOOGLE PAY E-Commerce
    PHONE_RECHARGE      = 'Phone Recharge'      # 'RICARICA TELEFONICA SERVIZIO INTERNET BANKING'

    # Income
    INCOMING_TRANSFER   = 'Incoming Transfer'   # 'BONIFICO A VOSTRO FAVORE'
    ACCOUNT_RECHARGE    = 'Account Recharge'    # 'RICARICA CONTO'
    MISC_CREDITS        = 'Miscellaneous Credits'  # 'ACCREDITI VARI'


class Unicredit(BankingSheet):
    iban: str|None
    card_last_4_digits: str|None
    importer_modules: list[Callable]

    def __init__(
            self,
            id: str,
            iban: str|None,
            name: str|None = None,
            card_last_4_digits: str|None = None,
            currency: str|None = None,
            importer_modules: list[Callable]|None = None
        ):
        from lib.framework import CONFIG
        super().__init__(id, currency or CONFIG.currency, name=name)
        self.iban = iban
        self.card_last_4_digits = card_last_4_digits
        self.data['unicredit_id'] = pd.Series([], dtype='string')
        self.data['unicredit_category'] = pd.Categorical([], categories=[c.value for c in UnicreditCategory])
        self.data['unicredit_original_desc'] = pd.Series([], dtype='string')
        if importer_modules is None:
            from lib.importers.unicredit_it import UNICREDIT_IT_MODULES
            self.importer_modules = UNICREDIT_IT_MODULES
        else:
            self.importer_modules = importer_modules

    def initialize(self, archive: Archive):
        # Load all the files from the archive into the in-memory balance sheet
        for id, record in archive.records[archive.records['sheet_name'] == self.id].iterrows():
            self.update_with_file(file, record) # type: ignore

    def merge_into(self, other: pd.DataFrame):
        # Merge the data from this balance sheet into another one
        other = pd.concat([other, self.data], ignore_index=True)
        return other

    def import_new_file(self, archive: Archive, filepath: str, date_range: DateRange|None = None):
        # If date_range is not provided, try to infer it from the file
        if date_range is None:
            df = pd.read_csv(filepath, sep=';', decimal=',', usecols=['Data Registrazione'])
            df['Data Registrazione'] = pd.to_datetime(df['Data Registrazione'], format='%d.%m.%Y')
            date_range = DateRange(
                df['Data Registrazione'].min(),
                df['Data Registrazione'].max()
            )
            del df # Manully unload the dataframe from memory as it might be big

        # Archive the file
        file_id = archive.archive_file(self.id, filepath, UNICREDIT_IMPORTER, date_range)

        # Update the in-memory balance sheet with the new file
        info: ArchiveRecord = archive.records.loc[file_id] # type: ignore
        self.update_with_file(filepath, info, check_hash=False)

    def update_with_file(self, csv_contents: str, info: ArchiveRecord, check_hash=False):
        if check_hash:
            raise Exception('Checking archive files hash is not implemented yet')

        # Load the data from the file and prepare it
        df = pd.read_csv(csv_contents, sep=';', decimal=',', usecols=['Data Registrazione', 'Descrizione', 'Importo (EUR)'])
        df.rename(columns={
            'Data Registrazione': 'date',
            'Descrizione': 'desc',
            'Importo (EUR)': 'amount',
        }, inplace=True)
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')
        df['archive_id'] = info.name # type: ignore

        for importer_module in self.importer_modules:
            df = importer_module(self, df)

        # Add the new data to the existing one
        self.data = pd.concat([self.data, df], ignore_index=True)

    # def _separate_description(self, df):
    #     for row in df['desc']:
    #         desc = []
    #         for i in range(0, len(row), 50):
    #             desc_slice = row[i:i+50]
    #             if row[i-1] == ' ' and i > 0 and row[i-2] != ' ':
    #                 desc[-1] += desc_slice
    #             else:
    #                 desc.append(desc_slice)
            
    #         match desc[0]:
                
