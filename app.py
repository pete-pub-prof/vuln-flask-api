import hashlib
import os
import sqlite3
from pathlib import Path

from flask import Flask, request, g
# from flask_api import status
from dataclasses import dataclass


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

    def destroy_user_database(self):
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

    def close_connection(self):
        self.con.commit()
        self.cursor.close()
        self.con.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.con.commit()
            self.con.close()
            # self.destroy_user_database()
        except Exception as e:
            print("Error Destroying User Database")
            print(e)
        finally:
            print(f"Destroyed User Database: {self.db_file}")


def init_app() -> Flask:
    app = Flask(__name__)
    app.config["user_db"] = UserDatabase("user_database.db")
    with app.app_context():
        g.db = UserDatabase("user.db")
    return app


def get_user_db() -> UserDatabase:
    if 'db' not in g:
        g.db = UserDatabase("user.db")
    return g.db


app = init_app()


@app.route('/user', methods=["POST"])
def create_user():  # put application's code here
    username: str = request.form["username"]
    password: str = request.form["password"]
    user = get_user_db().add(username, password)
    return {"id": user.id, "username": user.username}


@app.route("/user/login", methods=["POST"])
def login_user():
    username: str = request.form["username"]
    password: str = request.form["password"]
    try:
        user = get_user_db().get_authenticated_user(username, password)
    except ValueError as e:
        return {"error": "Authentication Failed"}, 401


@app.route("/", methods=["GET"])
def hello_world():
    get_user_db()._print_users()
    return "Hello World!", 200


if __name__ == '__main__':
    try:
        app.run()
    finally:
        get_user_db().destroy_user_database()
