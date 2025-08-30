from __future__ import annotations

import getpass
from flask import Flask

from app import create_app
from database import db
from models import User


def main():
    app: Flask = create_app()
    print("\n== To‑Do App Bootstrap ==\n")
    with app.app_context():
        # Tables are ensured by create_app() calling init_db().
        print("Database ready.")

        # Create user interactively
        print("Create an initial user.")
        username = input("Username: ").strip()
        while not username:
            username = input("Username (required): ").strip()

        if User.query.filter_by(username=username).first():
            print(f"User '{username}' already exists — nothing to do.")
            return

        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm:  ")
        while not password or password != confirm:
            print("Passwords do not match or empty. Try again.")
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm:  ")

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"User '{username}' created. You can now run the app.")


if __name__ == "__main__":
    main()
