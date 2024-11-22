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
from monjour.core.merge import MergeContext, Merger, DEFAULT_MERGE_EXECUTOR
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

    def import_file(self, account_id: str, filename: str|Path, date_range: DateRange|None,
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
        if isinstance(filename, Path):
            filename = str(filename)
        account = self.accounts[account_id]
        if date_range is None:
            with open(filename, 'rb') as f:
                date_range = account.importer.try_infer_daterange(f, filename)
        archive_id = Archive.calculate_archive_id(account.id, date_range)
        ctx = ImportContext(
            self.accounts[account_id],
            self.archive,
            archive_id,
            date_range=date_range,
            filename=filename,
            executor=executor,
        )
        ctx = account.import_file(ctx)
        ctx.log_all_diagnostics()

    def run(self):
        self.archive.load()
        self.load_all_from_archive()
        self.merge_accounts()

    ##############################################
    # Semi-Public API
    ##############################################

    def load_all_from_archive(self):
        for account in self.accounts.values():
            account.load_all_from_archive(self.archive)

    def merge_accounts(self, accounts: list[str]|None = None,
                       executor: Executor[MergeContext, pd.DataFrame] = DEFAULT_MERGE_EXECUTOR) -> MergeContext|None:
        """
        Create a master account by combining the specified accounts.

        Args:
            accounts: List of account IDs to merge. If None, all accounts are merged.
            merge_fn: Optional custom merge function to use instead of the default merge function.
        """
        # Filter and reorder the accounts to merge
        accounts_to_merge = [ self.accounts[id] for id in accounts or self.accounts.keys() ]

        if len(accounts_to_merge) == 0:
            log.warning("App.merge_accounts: No accounts to merge")
            return None

        # Setup
        df = pd.DataFrame() # Start with an empty dataframe
        ctx = MergeContext(self.categories, accounts_to_merge)
        block = executor.new_block((ctx, df))

        # Add all the mergers to the execution block, if the executor is an
        # ImmediateExecutor, this will run the mergers immediately
        # Otherwise, the mergers will be run when executor.run() is called
        for account in accounts_to_merge:
            block.exec(account.merger)
        self.df = block.last_result

        ctx.log_all_diagnostics()
        ctx.result = self.df
        return ctx

    ##############################################
    # Private API
    ##############################################

    def _archive_file(
            self,
            account_id: str,
            file: IO[bytes],
            filename: str,
            date_range: DateRange|None,
            executor: Executor[ImportContext, pd.DataFrame] = DEFAULT_IMPORT_EXECUTOR
    ) -> ImportContext:
        account = self.accounts[account_id]

        # Infer daterange if not provided
        if date_range is None:
            with open(filename, 'rb') as f:
                date_range = account.importer.try_infer_daterange(f, filename)

        # ArchiveID is deterministic and based on the account ID and the date range
        archive_id = Archive.calculate_archive_id(account.id, date_range)
        ctx = ImportContext(
            self.accounts[account_id],
            self.archive,
            archive_id,
            date_range=date_range,
            filename=filename,
            executor=executor,
        )
        ctx = account.archive_file(ctx, file)
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