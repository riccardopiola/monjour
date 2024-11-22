import pandas as pd
from typing import Callable, TYPE_CHECKING

from monjour.utils.diagnostics import DiagnosticCollector

if TYPE_CHECKING:
    from monjour.core.account import Account
