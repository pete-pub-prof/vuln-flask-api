import hashlib
import os
import sqlite3
from pathlib import Path

from flask import Flask
from dataclasses import dataclass

app = Flask(__name__)


@dataclass
class User:
    id: int
    username: str
    pw_hash: str


class UserDatabase:
    db_file: str
    con: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, db_filename: str):
        self.db_file = db_filename
        self.con = sqlite3.connect(db_filename)
        self.cursor = self.con.cursor()
        self._init_user_database()
        print(f"Initialized User Database: {self.db_file}")

    def _init_user_database(self):
        self.cursor.execute("""
        CREATE TABLE user(
            id INTEGER PRIMARY KEY, 
            username TEXT NOT NULL, 
            pw_hash TEXT NOT NULL
        )
        """)
        self.con.commit()

    def _destroy_user_database(self):
        self.cursor.execute("DELETE FROM user")
        self.cursor.execute("DROP TABLE user")
        self.cursor.close()
        self.con.close()
        if Path(self.db_file).exists():
            os.remove(self.db_file)

    @staticmethod
    def _hash(value: str) -> str:
        m = hashlib.sha1()
        m.update(value.encode('utf-8'))
        return m.hexdigest()

    def _add_user(self, username: str, pw_hash: str) -> User:
        res = self.cursor.execute("INSERT INTO user (username, pw_hash) VALUES (?, ?) RETURNING *;",
                                  (username, pw_hash))

        (res_id, res_username, res_pw_hash) = res.fetchone()
        self.con.commit()
        user = User(res_id, res_username, res_pw_hash)
        return user

    def add_user(self, username: str, password: str) -> User:
        pw_hash = self._hash(password)
        return self._add_user(username, pw_hash)

    def get_authenticated_user(self, username: str, password: str) -> User:
        pw_hash = self._hash(password)
        res = self.cursor.execute("""
        SELECT id, username, pw_hash FROM user WHERE username = ? AND pw_hash = ? ;
        """, (username, pw_hash))
        row = res.fetchone()
        if row is not None:
            (res_id, res_username, res_pw_hash) = row
            return User(res_id, res_username, res_pw_hash)
        else:
            raise ValueError("Could not authenticate user.")

    def _print_users(self):
        res = self.cursor.execute("SELECT * FROM user;")
        for row in res.fetchall():
            print(row)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._destroy_user_database()
        except Exception as e:
            print("Error Destroying User Database")
            print(e)
        finally:
            print(f"Destroyed User Database: {self.db_file}")


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
