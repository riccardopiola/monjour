from demo.gen.lib.common import *
from demo.gen.lib.routine import Routine
from gen.events import *
from demo.gen.lib.life import UniLife, Life


class UniRoutine(Routine):
    life: UniLife
    factory: UniFactory

    def __init__(self, date_range: tuple[datetime, datetime], life: UniLife):
        super().__init__(date_range, life, UniFactory(life))

