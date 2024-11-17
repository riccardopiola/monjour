import pandas as pd
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from monjour.core.account import Account

class MergeContext:
    df: pd.DataFrame
    current_account: "Account"

    merged: list["Account"]
    to_merge: list["Account"]

    def __init__(self, df: pd.DataFrame, first_acc: "Account"):
        self.df = df
        self.merged = []
        self.to_merge = []
        self.current_account = first_acc


MergerFn = Callable[[MergeContext, pd.DataFrame], pd.DataFrame]
