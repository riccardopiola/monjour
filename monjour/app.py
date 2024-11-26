import os
import json
from pathlib import Path
import pandas as pd
from typing import IO, Any, Callable

from monjour.core.executor import Executor
from monjour.core.log import MjLogger
from monjour.core.common import DateRange
from monjour.core.config import Config
from monjour.core.account import Account
from monjour.core.category import Category
from monjour.core.archive import Archive
from monjour.core.merge import MergeContext, Merger, DEFAULT_MERGE_EXECUTOR
from monjour.core.importer import ImportContext, DEFAULT_IMPORT_EXECUTOR

log = MjLogger(__name__)

class App:
    config: Config
    archive: Archive
    accounts: dict[str, Account]
    categories: dict[str, Category]

    df: pd.DataFrame # Master account
    df_listeners: list[Callable[[pd.DataFrame], None]] = []

    cli_args: dict[str, Any]

    ##############################################
    # Configuration
    ##############################################

    def __init__(self, config: Config, archive: Archive|None = None):
        self.config = config
        self.archive = Archive(Path(config.appdata_dir) / 'archive') if archive is None else archive
        self.accounts = {}
        self.categories = {}
        self.df = pd.DataFrame()
        self.df_listeners = []
        self.cli_args = json.loads(os.environ.get('MONJOUR_APP_ARGS', '{}'))

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

    def import_file(self, account_id: str, filename: str|Path, date_range: DateRange|None = None,
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
        importer = account.importer

        with open(filename, 'rb') as f:
            if date_range is None:
                date_range = importer.try_infer_daterange(f, filename)
            archive_id = self.archive.calculate_archive_id(account.id, f)
        ctx = ImportContext(
            self.accounts[account_id],
            self.archive,
            archive_id,
            date_range=date_range,
            filename=filename,
            importer_id=importer.info.id,
            executor=executor,
        )
        ctx = account.import_file(ctx)

    def run(self):
        log.info("App.run - Running app")
        self.archive.load()
        self.load_all_from_archive()
        self.merge_accounts()
        log.info("App.run - Done")

    ##############################################
    # Semi-Public API
    ##############################################

    def load_all_from_archive(self):
        for account in self.accounts.values():
            account.load_all_from_archive(self.archive)

    def merge_accounts(
        self,
        accounts: list[str]|None = None,
        executor: Executor[MergeContext, pd.DataFrame] = DEFAULT_MERGE_EXECUTOR
    ) -> MergeContext:
        """
        Create a master account by combining the specified accounts.

        Args:
            accounts: List of account IDs to merge. If None, all accounts are merged.
            executor: Executor to use for the merge process.
        """
        # Filter and reorder the accounts to merge
        accounts_to_merge = [ self.accounts[id] for id in accounts or self.accounts.keys() ]

        # Setup
        df = pd.DataFrame() # Start with an empty dataframe
        ctx = MergeContext(self.categories, accounts_to_merge)

        if len(accounts_to_merge) == 0:
            log.warning("App.merge_accounts: No accounts to merge")
            return ctx

        block = executor.new_block((ctx, df))
        # Add all the mergers to the execution block, if the executor is an
        # ImmediateExecutor, this will run the mergers immediately
        # Otherwise, the mergers will be run when executor.run() is called
        for account in accounts_to_merge:
            block.exec(account.merger)

        # Update the master account
        self.df = block.last_result
        ctx.result = self.df

        # Notify listeners
        for listener_fn in self.df_listeners:
            listener_fn(self.df)
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
        importer = account.importer

        archive_id = self.archive.calculate_archive_id(account.id, file)
        date_range = date_range or importer.try_infer_daterange(file, filename)
        ctx = ImportContext(
            self.accounts[account_id],
            self.archive,
            archive_id,
            date_range=date_range,
            filename=filename,
            importer_id=importer.info.id,
            executor=executor,
        )
        ctx = account.archive_file(ctx, file)
        return ctx

    def _add_df_listener(self, listener_fn: Callable[[pd.DataFrame], None]):
        """
        Add a listener that will be called whenever the master account (App.df) is updated.
        This occurs after a merge operation or a 
        """
        self.df_listeners.append(listener_fn)


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
        app.df = self.df
        app.df_listeners = self.df_listeners.copy()
        return app