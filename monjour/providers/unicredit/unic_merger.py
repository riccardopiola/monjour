import pandas as pd

from monjour.core.merge import MergeContext, merger

@merger()
def merge_unicredit(ctx: MergeContext, data: pd.DataFrame) -> pd.DataFrame:
    return data

