"""Reset an existing staff password locally and revoke that user's sessions."""
import argparse
from getpass import GetPassWarning, getpass
from pathlib import Path
import warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('username')
    parser.add_argument('--env-file', type=Path, help='Explicit configuration; existing environment takes precedence')
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        try:
            if not args.env_file.is_file():
                parser.error('Environment file does not exist')
            load_dotenv(args.env_file, override=False)
        except (OSError, UnicodeError):
            parser.error('Cannot read environment file')

    # Load configuration before importing the application's database engine.
    from pydantic import ValidationError
    from sqlalchemy import delete, update
    from sqlalchemy.exc import SQLAlchemyError
    from app.api.auth import LoginRequest
    from app.core.auth import hash_password, verify_password
    from app.db.session import SessionLocal
    from app.models.support import AuthSession, User

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', GetPassWarning)
            password = getpass('New password (12-128 characters): ')
            if password != getpass('Confirm password: '):
                parser.error('Passwords do not match')
    except (EOFError, KeyboardInterrupt, GetPassWarning):
        parser.exit(1, 'Password input cancelled or hidden input unavailable. No changes made.\n')
    try:
        payload = LoginRequest(username=args.username, password=password)
        if len(payload.password) < 12:
            raise ValueError('Password too short')
    except (ValidationError, ValueError):
        parser.error('Invalid account: username must use 1-64 letters/digits/_.-, password 12-128 characters')

    try:
        with SessionLocal.begin() as db:
            user = db.query(User).filter_by(username=payload.username).first()
            if user is None:
                parser.error('Username does not exist; use python -m app.create_user to create an account')
            if verify_password(payload.password, user.password_hash):
                parser.error('New password must differ from current password')
            result = db.execute(update(User).where(User.id == user.id, User.password_hash == user.password_hash)
                                .values(password_hash=hash_password(payload.password)))
            if result.rowcount != 1:
                parser.error('Password changed concurrently; retry')
            db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    except SQLAlchemyError:
        parser.exit(1, 'Reset failed. Check database configuration, schema and write access; retry after resolving the error.\n')
    print(f'Password reset: {payload.username}. All sessions revoked; role and active status unchanged.')


if __name__ == '__main__':
    main()
