from abc import ABC, abstractmethod
from pathlib import Path
from typing import Self
import pandas as pd
from datetime import datetime
from dataclasses import dataclass

from lib.archive import Archive, DateRange

CONFIG: "Config" = None # type: ignore

IMPORTERS: list["BalanceSheet"] = []
CATEGORIES: list["Category"] = []

@dataclass
class Config:
    name: str
    surname: str
    currency: str
    locale: str
    time_zone: str
    archive_dir: str
    cache_dir: str

    def __post_init__(self):
        global CONFIG
        CONFIG = self

class Category:
    name: str
    emoji: str|None
    children: list[str]

    def __init__(self, name, emoji: str|None = None, children: list[str]|list[Self] = []):
        self.name = name
        self.emoji = emoji
        if len(children) > 0:
            if isinstance(children[0], Category):
                self.children = list(map(lambda x: x.name, children)) # type: ignore
            else:
                self.children = children # type: ignore
        else:
            self.children = []

        CATEGORIES.append(self) # Self register

class BalanceSheet(ABC):
    id: str
    name: str|None
    data: pd.DataFrame
    locale: str

    def __init__(self, id: str, **kwargs):
        self.id = id
        self.name = kwargs.get('name')
        self.lang = kwargs.get('lang', CONFIG.locale)
        if 'skip_registration' not in kwargs:
            IMPORTERS.append(self) # Self register
        self.data = pd.DataFrame({
            'date':         pd.Series([], dtype='datetime64[s]'),
            'amount':       pd.Series([], dtype='float64'),
            'currency':     pd.Series([], dtype='string'),
            'desc':         pd.Series([], dtype='string'),
            'archive_id':   pd.Series([], dtype='string'),
            'category':     pd.Series([], dtype='string'),
            'payment_details': pd.Series([], dtype='string'), # Not always available
            'counterpart':  pd.Series([], dtype='string'), # Not always available
            'location':     pd.Series([], dtype='string'), # Not always available
        })

    @abstractmethod
    def initialize(self, archive: Archive):
        ...

    @abstractmethod
    def merge_into(self, other: pd.DataFrame):
        ...

    def import_new_file(self, archive: Archive, filepath: str, date_range: DateRange|None = None):
        raise Exception("Importing new files is not implemented supported")

class BankingSheet(BalanceSheet):
    currency: str

    def __init__(self, id: str, currency, **kwargs):
        super().__init__(id, **kwargs)
        self.currency = currency
        self.data['location'] = None
        self.data['payment_method'] = None
