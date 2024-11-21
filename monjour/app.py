from pathlib import Path
import pandas as pd
from typing import IO, Callable

from monjour.core.executor import Executor
import monjour.core.log as log
from monjour.core.common import DateRange
from monjour.core.config import Config
from monjour.core.account import Account
from monjour.core.category import Category
from monjour.core.archive import Archive
from monjour.core.merge import MergeContext, MergerFn
from monjour.core.importer import ImportContext, DEFAULT_IMPORT_EXECUTOR

class App:
    config: Config
    archive: Archive
    accounts: dict[str, Account]
    categories: dict[str, Category]
    df: pd.DataFrame # Master account

    ##############################################
    # Configuration
    ##############################################

    def __init__(self, config: Config, archive: Archive|None = None):
        self.config = config
        self.archive = Archive(Path(config.appdata_dir) / 'archive') if archive is None else archive
        self.accounts = {}
        self.categories = {}
        self.df = pd.DataFrame()

    def define_accounts(self, *accounts: Account):
        for account in accounts:
            account.initialize(self.config)
            self.accounts[account.id] = account

    def define_categories(self, *categories: Category):
        for category in categories:
            self.categories[category.name] = category

    ##############################################
    # Public API
    ##############################################

    @property
    def interactive(self):
        from monjour.replay.app_interactive import AppInteractive
        return AppInteractive(self)

    def import_file(self, account_id: str, file: str|Path, date_range: DateRange|None,
                    executor: Executor[ImportContext, pd.DataFrame] = DEFAULT_IMPORT_EXECUTOR):
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
        ctx = self.accounts[account_id].import_file(self.archive, file, date_range, executor)
        ctx.log_all_diagnostics()

    def run(self):
        self.archive.load()
        self.load_all_from_archive()
        self.combine_accounts()
        self.categorize()

    ##############################################
    # Semi-Public API
    ##############################################

    def load_all_from_archive(self):
        for account in self.accounts.values():
            account.load_all_from_archive(self.archive)

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

    ##############################################
    # Private API
    ##############################################

    def _archive_file(self, account_id: str, file: IO[bytes], filename: str, date_range: DateRange|None,
                    executor: Executor[ImportContext, pd.DataFrame] = DEFAULT_IMPORT_EXECUTOR) -> ImportContext:
        account = self.accounts[account_id]
        ctx = account.archive_file(self.archive, file, filename, date_range, executor)
        ctx.log_all_diagnostics()
        return ctx

    ##############################################
    # Utils
    ##############################################

    def copy(self):
        """
        Create a shallow copy of the app.
        """
        app = App(self.config, self.archive)
        app.accounts = self.accounts.copy()
        app.categories = self.categories.copy()
        return app