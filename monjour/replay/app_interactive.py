from typing import IO

from monjour.app import App
from monjour.core.common import DateRange
from monjour.core.importer import ImportContext

class AppInteractive:
    app: App

    def __init__(self, app: App):
        self.app = app

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.commit()

    def commit(self):
        pass

    def archive_file(self, account_id: str, file: IO[bytes], filename: str,
                     date_range: DateRange|None) -> ImportContext:
        account = self.app.accounts[account_id]
        ctx = account.archive_file(self.app.archive, file, filename, date_range)
        ctx.log_all_diagnostics()
        return ctx