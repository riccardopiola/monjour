from pathlib import Path
from typing import IO
from dataclasses import dataclass
import datetime as dt
import re
import warnings

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
        return DateRange(
            start=dt.datetime(year, month, 1),
            end=dt.datetime(year, month + 1, 1) - dt.timedelta(days=1)
        )

    @staticmethod
    def for_year(year: int):
        """
        Create a DateRange representing a whole year.
        """
        return DateRange(
            start=dt.datetime(year, 1, 1),
            end=dt.datetime(year, 12, 31)
        )

    @staticmethod
    def for_range(start: dt.datetime, end: dt.datetime, end_inclusive: bool=True):
        """
        Create a DateRange representing a range of dates.
        """
        if not end_inclusive:
            end = end - dt.timedelta(days=1)
        return DateRange(start=start, end=end)

def try_infer_daterange_from_filename(filename: str) -> DateRange:
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
    dates = []
    for m in re.finditer(r'(\d{4})-(\d{2})-(\d{2})', filename):
        dates.append(dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    if len(dates) != 2:
        raise ValueError(f'Could not infer date range from filename {filename}')
    return DateRange(dates[0], dates[1])