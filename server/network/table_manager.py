import logging
from server.game.table import Table
from shared.datatypes import Player
from shared.enums import GameState

STARTING_CHIPS = {1000: 0, 500: 0, 100: 5, 50: 10, 25: 0, 10: 50, 5: 0, 1: 0}


class TableManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.tables: dict[int, Table] = {}
        self.fd_to_player: dict[int, tuple[int, int]] = {}
        self.table_to_fds: dict[int, list[int]] = {}
        self._next_table_id = 1

    def create_table(
        self,
        owner_fd: int,
        owner_id: int,
        owner_name: str,
        owner_avatar: int,
        big_blind: int = 20,
    ) -> int:
        table_id = self._next_table_id
        self._next_table_id += 1
        owner = Player(owner_id, owner_name, owner_avatar, STARTING_CHIPS)
        table = Table(owner, STARTING_CHIPS, big_blind)
        self.tables[table_id] = table
        self.table_to_fds[table_id] = [owner_fd]
        self.fd_to_player[owner_fd] = (table_id, owner_id)
        self.logger.info(
            f"table {table_id} created by player {owner_name} (id={owner_id})"
        )
        return table_id

    def delete_table(self, table_id: int):
        if table_id not in self.tables:
            return
        fds = self.table_to_fds.pop(table_id, [])
        for fd in fds:
            self.fd_to_player.pop(fd, None)
        del self.tables[table_id]
        self.logger.info(f"table {table_id} deleted")

    def get_table(self, table_id: int) -> Table | None:
        return self.tables.get(table_id)

    def add_player_to_table(
        self,
        table_id: int,
        player_id: int,
        player_name: str,
        player_avatar: int,
        client_fd: int,
    ):
        if table_id not in self.tables:
            raise ValueError(f"Table {table_id} does not exist")
        table = self.tables[table_id]
        player = Player(player_id, player_name, player_avatar, STARTING_CHIPS)
        table.add_player(player)
        self.fd_to_player[client_fd] = (table_id, player_id)
        self.table_to_fds.setdefault(table_id, []).append(client_fd)
        self.logger.info(f"player {player_name} added to table {table_id}")

    def remove_player_by_fd(self, fd: int):
        if fd not in self.fd_to_player:
            return
        table_id, player_id = self.fd_to_player.pop(fd)
        table = self.tables.get(table_id)
        if table:
            if table.game_state != GameState.WAITING:
                current = table.players[table.current_player_idx]
                if current.id == player_id:
                    try:
                        table.process_player_action(player_id, "fold")
                        self.logger.info(
                            f"auto-fold for disconnected player {player_id}"
                        )
                    except Exception:
                        pass
            table.remove_player(player_id)
            fds = self.table_to_fds.get(table_id, [])
            if fd in fds:
                fds.remove(fd)
            if not table.players:
                self.delete_table(table_id)
                self.logger.info(f"table {table_id} deleted")

    def get_table_id_by_fd(self, fd: int) -> int | None:
        mapping = self.fd_to_player.get(fd)
        return mapping[0] if mapping else None

    def get_player_id_by_fd(self, fd: int) -> int | None:
        mapping = self.fd_to_player.get(fd)
        return mapping[1] if mapping else None

    def get_fds_at_table(self, table_id: int) -> list[int]:
        return self.table_to_fds.get(table_id, []).copy()

    def get_all_tables(self) -> dict[int, Table]:
        return self.tables.copy()

    def get_tables(self) -> list[dict]:
        return [
            {
                "table_id": table_id,
                "owner": table.owner.name,
                "num_players": len(table.players),
                "max_players": table.max_players,
                "big_blind": table.big_blind,
                "game_state": table.game_state.name,
            }
            for table_id, table in self.tables.items()
            if table.game_state == GameState.WAITING
        ]
