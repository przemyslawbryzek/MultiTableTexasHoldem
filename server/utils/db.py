from dataclasses import dataclass
import sqlite3


@dataclass
class User:
    id: int
    username: str
    password: str


con = sqlite3.connect("server.db")
cur = con.cursor()


def init(*, drop=False):
    if drop:
        cur.execute("DROP TABLE IF EXISTS user")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS user ("
        "id INTEGER PRIMARY KEY,"
        "username TEXT UNIQUE NOT NULL,"
        "password TEXT NOT NULL"
        ")"
    )


def create_user(username: str, password: str) -> User | None:
    try:
        cur.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            (username, password),
        )
        con.commit()
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            return None
        else:
            raise
    return User(cur.lastrowid, username, password)


def get_user(username: str) -> User | None:
    res = cur.execute(
        "SELECT id, username, password FROM user WHERE username = ?",
        (username,),
    )
    row = res.fetchone()
    if row is None:
        return None
    id, username, password = row
    return User(id, username, password)


def delete_user(id: int) -> bool:
    cur.execute("DELETE FROM user WHERE id = ?", (id,))
    con.commit()
    return cur.rowcount == 1
