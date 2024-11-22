from pathlib import Path
from typing import IO
from dataclasses import dataclass
import datetime as dt
import re
import warnings
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning, message="The behavior of array concatenation with empty entries is deprecated")

PathOrBuffer = str|Path|IO[bytes]

@dataclass
class DateRange:
    """
    A time period with a start and end date
    """
    start: dt.datetime
    end: dt.datetime

    @staticmethod
    def for_month_year(month: int, year: int):
        """
        Create a DateRange representing a month of a specific year.
        """
        end_month = month + 1 if month < 12 else 1
        return DateRange(
            start = dt.datetime.combine(dt.date(year, month, 1), dt.time.min),
            end = dt.datetime.combine(dt.date(year, end_month, 1), dt.time.max) - dt.timedelta(days=1)
        )

    @staticmethod
    def for_year(year: int):
        """
        Create a DateRange representing a whole year.
        """
        return DateRange(
            start=dt.datetime.combine(dt.date(year, 1, 1), dt.time.min),
            end=dt.datetime.combine(dt.datetime(year, 12, 31), dt.time.max)
        )

    @staticmethod
    def for_range(start: dt.datetime, end: dt.datetime, end_inclusive: bool=True):
        """
        Create a DateRange representing a range of dates.
        """
        if not end_inclusive:
            end = end - dt.timedelta(seconds=1)
        return DateRange(start=start, end=end)

    @staticmethod
    def from_strings(start: str, end: str):
        """
        Create a DateRange from two strings in the format 'YYYY-MM-DD'.
        """
        return DateRange(
            start=dt.datetime.strptime(start, '%Y-%m-%d'),
            end=dt.datetime.combine(dt.datetime.strptime(end, '%Y-%m-%d'), dt.time.max)
        )

def try_infer_daterange_from_filename(filename: str) -> DateRange|None:
    """
    Try to infer the date range from the filename.
    This function scans the filename for two dates in the format 'YYYY-MM-DD' and returns a DateRange object.

    Args:
        filepath: Path to the file to infer the date range from.

    Returns:
        DateRange object with the inferred date range.

    Raises:
        ValueError: If the date range could not be inferred
    """
    # Find two dates in the filename
    matches = re.findall(r'\d{4}-\d{2}-\d{2}', filename)
    if len(matches) != 2:
        return None
    start = dt.datetime.strptime(matches[0], '%Y-%m-%d')
    end = dt.datetime.combine(dt.datetime.strptime(matches[1], '%Y-%m-%d'), dt.time.max)
    return DateRange(start=start, end=end)