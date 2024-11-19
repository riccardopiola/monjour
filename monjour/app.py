from pathlib import Path
import pandas as pd
from typing import IO, Callable

import monjour.core.log as log
from monjour.core.common import DateRange
from monjour.core.config import Config
from monjour.core.account import Account
from monjour.core.category import Category
from monjour.core.archive import Archive
from monjour.core.merge import MergeContext, MergerFn

class App:
    config: Config
    archive: Archive
    accounts: dict[str, Account]
    categories: dict[str, Category]
    df: pd.DataFrame # Master account

    ##############################################
    # Configuration
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
    # API
    ##############################################

    @property
    def interactive(self):
        from monjour.replay.app_interactive import AppInteractive
        return AppInteractive(self)

    def import_file(self, account_id: str, file: str|Path, date_range: DateRange|None):
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
        ctx = self.accounts[account_id].import_file(self.archive, file, date_range)
        ctx.log_all_diagnostics()

    def run(self):
        self.combine_accounts()
        self.categorize()

    ##############################################
    # API Details
    ##############################################

    def combine_accounts(self, accounts: list[str]|None = None,
                         merge_fn: MergerFn|None = None) -> MergeContext:
        """
        Create a master account by combining the specified accounts.

        Args:
            accounts: List of account IDs to merge. If None, all accounts are merged.
            merge_fn: Optional custom merge function to use instead of the default merge function.
        """
        df = pd.DataFrame() # Create a new empty DataFrame
        ctx = MergeContext()

        if len(self.accounts) == 0:
            log.warning("combine_accounts: No accounts to merge")

        # Filter and reorder the accounts to merge
        accounts_to_merge = [ self.accounts[id] for id in accounts or self.accounts.keys() ]

        # Create the merge context
        ctx.to_merge = accounts_to_merge.copy()
        # Merge all the accounts in order
        for account in accounts_to_merge:
            ctx.advance()
            # Let the account perform the merge
            if merge_fn:
                df = merge_fn(ctx, df)
            else:
                df = account.merge(ctx, df)
        ctx.log_all_diagnostics()
        return ctx

    def categorize(self):
        pass
