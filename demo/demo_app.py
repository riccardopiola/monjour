import sys
import os
import subprocess
from pathlib import Path

from monjour import *
from monjour.utils import console
from monjour.core.log import MjLogger

log = MjLogger(__name__)

PROJECT_DIR = Path(__file__).parent
GEN_DIR = PROJECT_DIR / 'gen'

class DemoApp(App):

    def __init__(self, config: Config, archive: Archive|None = None):
        super().__init__(config, archive)
        if self.cli_args.get('regen'):
            log.info("Found commandline gen flag. Regenerating data...")
            self.gen_data()
        elif not Path(GEN_DIR / 'out' / 'bank_2021.csv').exists():
            log.info("Data not found. Generating data...")
            self.gen_data()

    def gen_data(self):
        python_exe = sys.executable
        if console.launch_program([python_exe, '-m', 'gen'], cwd=PROJECT_DIR, window=True, close_shell=True) != 0:
            raise Exception("Failed to generate data.")
        log.info("Data generated successfully.")




