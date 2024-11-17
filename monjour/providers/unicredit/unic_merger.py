import pandas as pd

from monjour.core.merge import MergeContext

def merge_unicredit(ctx: MergeContext, data: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([data, ctx.df])

