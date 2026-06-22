from dataclasses import dataclass
import sqlite3
import os
import pathlib


@dataclass
class User:
    id: int
    username: str
    password: str


class DB:
    def __init__(self, *, drop=False):
        dir = pathlib.Path(__file__).parent.resolve()
        self.con = sqlite3.connect(os.path.join(dir, "sqlite3.db"))
        self.cur = self.con.cursor()
        if drop:
            self.cur.execute("DROP TABLE IF EXISTS user")
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS user ("
            "id INTEGER PRIMARY KEY,"
            "username TEXT UNIQUE NOT NULL,"
            "password TEXT NOT NULL"
            ")"
        )

    def create_user(self, username: str, password: str) -> User | None:
        try:
            self.cur.execute(
                "INSERT INTO user (username, password) VALUES (?, ?)",
                (username, password),
            )
            self.con.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                return None
            else:
                raise
        return User(self.cur.lastrowid, username, password)

    def get_user(self, username: str) -> User | None:
        res = self.cur.execute(
            "SELECT id, username, password FROM user WHERE username = ?",
            (username,),
        )
        row = res.fetchone()
        if row is None:
            return None
        id, username, password = row
        return User(id, username, password)

    def delete_user(self, id: int) -> bool:
        self.cur.execute("DELETE FROM user WHERE id = ?", (id,))
        self.con.commit()
        return self.cur.rowcount == 1
