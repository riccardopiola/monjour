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
    """
    Context object that is passed to the various classes partecipating in the merge process.
    This object contains all the information a Merger might need to merge one account into the main DataFrame.

    Similiarly to ImportContext
    - The context is mostly immutable, with the exception of the result and 'extra' fields.
    - The context collects diagnostics that are generated during the merge process.
    - The context doubles as the object representing the result of the merge operation.

    Attributes:
        accounts:   List of accounts that are being merged.
        categories: Categories defined in the app.
        extras:     Extra information that can be passed to the merger or within modules of a merger.
        executor:   Executor that will be used to execute the merge process.
        result:     Result of the merge process. This field is set at the end of the merge process.
    """
    # Accounts being merged toghether
    accounts: list["Account"]

    # Index of the current account being merged
    _cur_account_index: int

    # Categories defined in the app
    categories: dict[str, Category]

    # Extra data that can be passed around
    extras: dict

    # Executor being used for the merge operation
    executor: Executor

    # Return value of the final transformation
    result: pd.DataFrame|None

    def __init__(self, categories: dict[str, Category], accounts_to_merge: list["Account"],
                 extras: dict|None = None):
        super().__init__('MergeContext')
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

    def _diag_prefix(self) -> str:
        return self.current_account.id + ' merger: '

# Official type for Merger object. Its really just a wrapper
# for a fn of type (MergeContext, pd.DataFrame) -> pd.DataFrame
Merger = Transformer[MergeContext, pd.DataFrame]

class BoundMerger(Transformer[MergeContext, pd.DataFrame]):
    """
    Merger bound to a specific account type.
    This is used to ensure that the merger is only used with the correct account type.
    """
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