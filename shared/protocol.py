import json
import struct
from shared.enums import MessageType, ActionType
from typing import TypedDict, Optional


class Protocol:
    HEADER_SIZE = 4

    @staticmethod
    def encode_message(msg: dict) -> bytes:
        payload = json.dumps(msg).encode("utf-8")
        header = struct.pack(">I", len(payload))
        return header + payload

    @staticmethod
    def extract_message(buffer: bytes) -> tuple[Optional[dict], bytes]:
        if len(buffer) < Protocol.HEADER_SIZE:
            return None, buffer

        length = struct.unpack(">I", buffer[: Protocol.HEADER_SIZE])[0]

        if len(buffer) < Protocol.HEADER_SIZE + length:
            return None, buffer

        payload = buffer[Protocol.HEADER_SIZE : Protocol.HEADER_SIZE + length]
        remaining = buffer[Protocol.HEADER_SIZE + length :]

        try:
            msg = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            return None, remaining

        return msg, remaining


class GetTablesMessage(TypedDict):
    type: str


class JoinTableMessage(TypedDict):
    type: str
    table_id: int
    player_name: str
    player_id: int


class CreateTableMessage(TypedDict):
    type: str
    player_name: str
    player_id: int
    big_blind: int


class StartTableMessage(TypedDict):
    type: str


class ActionMessage(TypedDict):
    type: str
    action: str
    amount: Optional[int]


class CreateAccountMessage(TypedDict):
    type: str
    username: str
    password: str


class LoginMessage(TypedDict):
    type: str
    username: str
    password: str


class PlayerInfo(TypedDict):
    id: int
    name: str
    chips: int
    bet: int
    is_folded: bool
    is_all_in: bool
    is_active: bool
    hand: list[str]


class GameStateMessage(TypedDict):
    type: str
    game_state: str
    players: list[PlayerInfo]
    community_cards: list[str]
    pot: int
    current_player: int
    highest_bet: int
    small_blind: int
    big_blind: int


class PlayerJoinedMessage(TypedDict):
    type: str
    player: PlayerInfo


class GameStartMessage(TypedDict):
    type: str


class HandEndMessage(TypedDict):
    type: str
    winners: list[dict]


class ErrorMessage(TypedDict):
    type: str
    message: str
