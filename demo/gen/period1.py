from gen.common import *
from gen.routine import Routine
from gen.factory import Weights, Factory
from gen.events import *
from gen.life import UniLife, Life
from gen.factory import UniFactory

UNI_WEIGHTS = Weights({
    'coffee'              : RoutineEvent(constant(2), daily=0.4),
    'withdrawal'          : RoutineEvent(normal(50, 10), daily=0.15),
    'online_purchase'     : RoutineEvent(normal(50, 10), daily=0.1),
    'transport'           : RoutineEvent(normal(2, 0.5), daily=1.0),

    'night_out'           : RoutineEvent(constant(50), weekly=0.2),
    'groceries'           : RoutineEvent(normal(40, 10), weekly=0.8),

    'book_purchase'       : RoutineEvent(normal(20, 5), monthly=0.5),
    'rent'                : MonthlyFixture(500),
    'gym_membership'      : MonthlyFixture(30),
    'phone_bill'          : MonthlyFixture(10),
    'allowance'           : MonthlyFixture(200)
})

class UniRoutine(Routine):
    life: UniLife
    factory: UniFactory

    def __init__(self, date_range: tuple[datetime, datetime], life: UniLife):
        super().__init__(date_range, life, UniFactory(life))

