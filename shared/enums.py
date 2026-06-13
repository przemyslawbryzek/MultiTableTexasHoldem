from enum import Enum
class GameState(Enum):
    WAITING = 1
    PRE_FLOP = 2
    FLOP = 3
    TURN = 4
    RIVER = 5
    SHOWDOWN = 6