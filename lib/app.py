from pathlib import Path
from typing import Callable
import pandas as pd

import lib.core.log as log
from lib.core.common import try_infer_daterange_from_filename, DateRange
from lib.core.config import Config
from lib.core.account import Account
from lib.core.category import Category
from lib.core.archive import Archive
from lib.core.merge import MergeContext, MergerFn

class App:
    config: Config
    archive: Archive
    accounts: dict[str, Account]
    categories: dict[str, Category]
    df: pd.DataFrame # Master account

    ##############################################
    # Definitions
    ##############################################

    def __init__(self, config: Config):
        self.config = config
        self.archive = Archive(config)
        self.accounts = {}
        self.categories = {}
        self.df = pd.DataFrame()

    def define_accounts(self, *accounts: Account):
        for account in accounts:
            self.accounts[account.id] = account
            account.initialize(self.config, self.archive)

    def define_categories(self, *categories: Category):
        for category in categories:
            self.categories[category.name] = category

    ##############################################
    # Run
    ##############################################

    def import_file(self, account_id: str, file: str|Path, date_range: DateRange|None = None):
        """
        Import a file into the account with the given ID.

        Args:
            account_id: ID of the account to import the file into.
            file:       Path to the file to import.
            date_range: Optional date range to associate with the file. If not provided,
                        the date range will be inferred from the filename.
        Throws:
            ValueError: If the account ID is not found.
            ValueError: If the date range cannot be inferred from the filename and none is provided.
        """
        if isinstance(file, str):
            file = Path(file)
        if date_range is None:
            date_range = try_infer_daterange_from_filename(file.name)
        self.accounts[account_id].import_file(self.archive, file, date_range)

    def combine_accounts(self, include: list[str] = [], exclude: list[str] = [], order: list[str] = [],
                         merge_fn: MergerFn|None = None):
        """
        Create a master account by combining all the accounts in the app.

        Args:
            include:    List of account IDs to include in the merge. If empty, all accounts are included.
            exclude:    List of account IDs to exclude from the merge. If empty, no accounts are excluded.
            order:      List of account IDs to specify the order of the merge. If empty, the order in which
                        the accounts were defined is used.
        """
        self.df = pd.DataFrame() # Reset the master sheet

        if len(self.accounts) == 0:
            log.warning("No accounts defined. Nothing to merge.")
            return self.df

        # Filter and reorder the accounts to merge
        account_ids = list(self.accounts.keys())
        if len(order) > 0:
            account_ids = sorted(account_ids, key=lambda x: order.index(x) if x in order else len(order))
        if len(include) > 0:
            account_ids = [x for x in account_ids if x in include]
        if len(exclude) > 0:
            account_ids = [x for x in account_ids if x not in exclude]
        accounts_to_merge = [ self.accounts[account_id] for account_id in account_ids ]

        # Create the merge context
        ctx = MergeContext(self.df, accounts_to_merge[0])
        ctx.to_merge = accounts_to_merge.copy()
        # Merge all the accounts in order
        for account in accounts_to_merge:
            # Let the account perform the merge
            if merge_fn:
                ctx.df = merge_fn(ctx, account.data)
            else:
                ctx.df = account.merge(ctx)
            # Update the merge context
            ctx.to_merge.pop(0)
            ctx.merged.append(account)
        return self.df

    def categorize(self):
        pass
