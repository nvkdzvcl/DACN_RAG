"""Run python -m app.create_user USERNAME --role admin to provision staff locally."""
import argparse
from getpass import getpass

from fastapi import HTTPException
from pydantic import ValidationError
from app.api.auth import UserCreate, create_user
from app.db.migrations import migrate
from app.db.session import SessionLocal, engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    parser.add_argument("--role", choices=["admin", "agent"], default="agent")
    parser.add_argument("--name")
    args = parser.parse_args()
    password = getpass("Password (12-128 characters): ")
    if password != getpass("Confirm password: "):
        parser.error("Passwords do not match")
    try:
        payload = UserCreate(username=args.username, password=password, display_name=args.name or args.username, role=args.role)
    except ValidationError:
        parser.error("Invalid account: username must use letters/digits/_.-, name 1-160 characters, password 12-128 characters")
    migrate(engine)
    with SessionLocal() as db:
        try:
            user = create_user(db, payload)
        except HTTPException as exc:
            parser.error(exc.detail)
        print(f"Created {user.role}: {user.username}")


if __name__ == "__main__":
    main()
