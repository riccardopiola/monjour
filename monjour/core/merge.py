import pandas as pd
import copy
from typing import TYPE_CHECKING, Callable

from monjour.core.executor import Executor
from monjour.core.transformation import Transformer
from monjour.core.category import Category
from monjour.core.executor import Executor
from monjour.utils.diagnostics import DiagnosticCollector

if TYPE_CHECKING:
    from monjour.core.account import Account

DEFAULT_MERGE_EXECUTOR = Executor["MergeContext", pd.DataFrame]()

class MergeContext(DiagnosticCollector):
    # Accounts being merged toghether
    accounts: list["Account"]

    # Index of the current account being merged
    _cur_account_index: int

    # Categories defined in the app
    categories: dict[str, Category]

    # Extra data that can be passed around
    extras: dict

    # Return value of the final transformation
    result: pd.DataFrame|None

    # Executor being used for the merge operation
    executor: Executor

    def __init__(self, categories: dict[str, Category], accounts_to_merge: list["Account"],
                 extras: dict|None = None):
        super().__init__()
        self.accounts = accounts_to_merge
        self._cur_account_index = 0
        self.result = None
        self.categories = categories
        self.extras = extras or dict()

    @property
    def current_account(self) -> "Account":
        """Current account being merged."""
        return self.accounts[self._cur_account_index]

    @property
    def accounts_to_merge(self):
        """Accounts that still need to be merged."""
        return self.accounts[self._cur_account_index:]

    @property
    def accounts_merged(self):
        """Accounts that have already been merged."""
        return self.accounts[:self._cur_account_index]

    def is_merged(self, account_id: str) -> bool:
        """Check if an account has already been merged."""
        return any(account.id == account_id for account in self.accounts[:self._cur_account_index])

    def copy(self):
        """Creates a shallow copy of the MergeContext object."""
        ctx = MergeContext(self.categories, self.accounts, extras=copy.deepcopy(self.extras))
        ctx._cur_account_index = self._cur_account_index
        return ctx

# Official type for Merger object. Its really just a wrapper
# for a fn of type (MergeContext, pd.DataFrame) -> pd.DataFrame
Merger = Transformer[MergeContext, pd.DataFrame]

class BoundMerger(Transformer[MergeContext, pd.DataFrame]):
    bound_account: "type[Account]"
    bound_instance: "Account|None"

    def __init__(
        self,
        fn: Callable[[MergeContext, pd.DataFrame], pd.DataFrame],
        bound: "type[Account]",
        bound_instance: "Account|None" = None,
        name: str|None = None,
    ):
        if name is None:
            name = f"{bound.id}_merger"
        super().__init__(fn, name)
        self.bound_account = bound
        self.bound_instance = bound_instance

    def __call__(self, ctx: MergeContext, data: pd.DataFrame) -> pd.DataFrame:
        if self.bound_instance is not None:
            if ctx.current_account is not self.bound_instance:
                raise ValueError(f"Merger '{self.name}' is bound to account '{self.bound_instance.id}' but being called on '{ctx.current_account.id}'")
        elif type(ctx.current_account) is not self.bound_account:
            raise ValueError(f"Merger '{self.name}' is bound to account '{self.bound_account.__class__.__name__}' but being called on '{ctx.current_account.__class__.__name__}'")
        result = self.fn(ctx, data)
        ctx._cur_account_index += 1
        return result

def merger(name: str|None = None, bound: "type[Account]|None" = None):
    """
    Decorator for Merger functions.
     - It wraps the function in a Transformer object and sets the name attribute.
     - It also makes sure the function signature is correct. (if editor type checking is enabled)
     - It's technically the same as the transformer decorator, but with predefined generic types.

    Args:
        name: Optional name for the merger. If not provided, the name of the function will be used.

    Returns:
        Decorator function turning a function into a Transformer object.
    """
    def decorator(fn: Callable[[MergeContext, pd.DataFrame], pd.DataFrame]) -> Merger:
        if bound:
            return BoundMerger(fn, bound, None, name or fn.__name__)
        else:
            return Merger(fn, name)
    return decorator