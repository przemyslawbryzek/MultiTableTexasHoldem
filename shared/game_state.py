from dataclasses import dataclass, field, asdict
from typing import Optional, List
from shared.enums import GameState as GamePhase, ActionType

@dataclass
class PlayerState:
    id: int
    name: str
    avatar: int
    chips: dict[int, int]
    bet_this_round: int
    total_bet_this_hand: int
    is_active: bool
    is_folded: bool
    is_all_in: bool
    position: int
    hand: List[str]
    hand_size: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SidePotState:
    amount: int
    eligible_players: List[int]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AvailableAction:
    action: ActionType
    min_amount: int
    max_amount: int
    label: str

    def to_dict(self) -> dict:
        return {
            "action": self.action.value if isinstance(self.action, ActionType) else self.action,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "label": self.label,
        }


@dataclass
class GameState:
    phase: GamePhase
    owner_id: int
    hand_number: int
    dealer_position: int
    current_player_id: int
    small_blind: int
    big_blind: int
    highest_bet: int
    last_raise: int
    pot: int
    side_pots: List[SidePotState]
    community_cards: List[str]
    players: List[PlayerState]
    available_actions: List[AvailableAction]

    def to_dict(self) -> dict:
        return {
            "type": "STATE",
            "game_state": self.phase.value,
            "hand_number": self.hand_number,
            "dealer_position": self.dealer_position,
            "current_player_id": self.current_player_id,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "highest_bet": self.highest_bet,
            "last_raise": self.last_raise,
            "pot": self.pot,
            "side_pots": [sp.to_dict() for sp in self.side_pots],
            "community_cards": self.community_cards,
            "players": [p.to_dict() for p in self.players],
            "available_actions": [a.to_dict() for a in self.available_actions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        return cls(
            phase=GamePhase(data["game_state"]),
            hand_number=data.get("hand_number", 0),
            owner_id=data.get("owner_id", 0),
            dealer_position=data["dealer_position"],
            current_player_id=data["current_player_id"],
            small_blind=data["small_blind"],
            big_blind=data["big_blind"],
            highest_bet=data["highest_bet"],
            last_raise=data["last_raise"],
            pot=data["pot"],
            side_pots=[
                SidePotState(amount=sp["amount"], eligible_players=sp["eligible_players"])
                for sp in data.get("side_pots", [])
            ],
            community_cards=data.get("community_cards", []),
            players=[
                PlayerState(
                    id=p["id"],
                    name=p["name"],
                    avatar=p["avatar"],
                    chips=p["chips"],
                    bet_this_round=p["bet_this_round"],
                    total_bet_this_hand=p.get("total_bet_this_hand", 0),
                    is_active=p["is_active"],
                    is_folded=p["is_folded"],
                    is_all_in=p["is_all_in"],
                    position=p.get("position", 0),
                    hand=p["hand"],
                    hand_size=p["hand_size"],
                )
                for p in data["players"]
            ],
            available_actions=[
                AvailableAction(
                    action=ActionType(a["action"]),
                    min_amount=a["min_amount"],
                    max_amount=a["max_amount"],
                    label=a["label"],
                )
                for a in data.get("available_actions", [])
            ],
        )