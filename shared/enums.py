from enum import Enum
class GameState(Enum):
    WAITING = 1
    PRE_FLOP = 2
    FLOP = 3
    TURN = 4
    RIVER = 5
    SHOWDOWN = 6

class MessageType(str, Enum):
    # Client -> Server
    ACTION = "action"
    GET_TABLES = "get_tables"
    JOIN_TABLE = "join_table"
    CREATE_TABLE = "create_table"
    START_TABLE = "start_table"
    CREATE_ACCOUNT = "create_account"
    LOGIN = "login"
    # Server -> Client
    STATE = "state"
    ERROR = "error"
    PLAYER_JOINED = "player_joined"
    GAME_START = "game_start"
    HAND_END = "hand_end"
    # Responses
    LOGIN_RESPONSE          = "login_response"
    CREATE_ACCOUNT_RESPONSE = "create_account_response"
    CREATE_TABLE_RESPONSE   = "create_table_response"
    JOIN_TABLE_RESPONSE     = "join_table_response"
    ACTION_RESPONSE         = "action_response"
    GET_TABLES_RESPONSE     = "get_tables_response"
    START_TABLE_RESPONSE      = "start_table_response"

class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all-in"