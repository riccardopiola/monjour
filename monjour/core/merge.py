import pandas as pd
from typing import Callable, TYPE_CHECKING

from monjour.utils.diagnostics import DiagnosticCollector

if TYPE_CHECKING:
    from monjour.core.account import Account

class MergeContext(DiagnosticCollector):
    cur_acc: "Account|None" = None

    merged: list["Account"]
    to_merge: list["Account"]

    def __init__(self):
        super().__init__()
        self.merged = []
        self.to_merge = []

    def cur_acc_or_raise(self) -> "Account":
        if self.cur_acc is None:
            raise ValueError("No current account")
        return self.cur_acc

    def cur_df_or_raise(self) -> pd.DataFrame:
        if self.cur_acc is None:
            raise ValueError("No current account")
        return self.cur_acc.data

    def advance(self):
        if self.cur_acc is None:
            self.cur_acc = self.to_merge.pop(0)
        else:
            self.merged.append(self.cur_acc)
            self.cur_acc = self.to_merge.pop(0)

MergerFn = Callable[[MergeContext, pd.DataFrame], pd.DataFrame]
