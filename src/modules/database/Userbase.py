from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from modules.blockchain.Signature import generate_keys
from modules.tools.utils import compute_hash
from cryptography.hazmat.primitives import serialization
from modules.database.User import User
from sqlalchemy.exc import OperationalError
from InquirerPy import inquirer
from InquirerPy.validator import PasswordValidator
from modules.networking.wallet_network.wallet_client import Request

import os

Base = declarative_base()
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATABASE_DIR = os.path.join(PROJECT_DIR, "data")
DATABASE_FILE = "goodchain.db"
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_FILE)
DATABASE_NAME = f"sqlite:///{DATABASE_PATH}"

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    private_key = Column(LargeBinary, nullable=False)


engine = create_engine(DATABASE_NAME)
Session = sessionmaker(bind=engine)


def create_tables():
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    Base.metadata.create_all(engine)


def register_user(username, password):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()  # Créez une instance de Session ici

    try:
        # Check if the user already exists
        existing_user = (
            session.query(UserModel).filter_by(username=username).first()
        )
        if existing_user:
            print("Username already exists. Please choose another username.")
            return False

        # Hash the password and generate keys
        password_hash = compute_hash(password)
        private_key, public_key = generate_keys()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Create new user instance and add to the session
        user = UserModel(
            username=username,
            password_hash=password_hash,
            public_key=public_key,
            private_key=private_key_pem,
        )
        session.add(user)
        session.flush()  # Ensure that the user is flushed to the DB
        session.commit()  # Commit changes to the database
        Request.broadcast_user_registration(user)
        return True  # Successfully registered

    except Exception as e:
        print(f"Error registering user: {e}")
        session.rollback()
        return False

    finally:
        session.close()


def add_user(user_data):
    session = Session()
    try:
        existing_user = session.query(UserModel).filter_by(username=user_data.username).first()
        if existing_user:
            print("User already exist !")
            return False
        
        new_user = UserModel(
            username=user_data.username,
            password_hash=user_data.password_hash,
            public_key=user_data.public_key,
            private_key=user_data.private_key,
        )
        session.add(new_user)
        session.commit()  # Commit changes here
        return True
        
    except Exception as e:
        print(f"Error registering user: {e}")
        session.rollback()
        return False

    finally:
        session.close()
 # Make sure to close session here


def get_all_users():
    session = Session()

    user_rows = session.query(UserModel).all()

    session.close()

    if user_rows:
        return user_rows

    return None

def user_exists(user_data):
    session = Session()
    try:
        existing_user = session.query(UserModel).filter_by(username=user_data.username).first()
        return existing_user is not None
    finally:
        session.close()


def get_username_by_public_key(public_key):
    session = Session()

    user_row = session.query(UserModel).filter_by(public_key=public_key).first()

    session.close()

    if user_row:
        return user_row.username

    return None


def get_user_by_credentials(username, password):
    session = Session()

    password_hash = compute_hash(password)
    user_row = (
        session.query(UserModel)
        .filter_by(username=username, password_hash=password_hash)
        .first()
    )

    session.close()

    if user_row:
        user = User()
        user.username = user_row.username
        user.password_hash = user_row.password_hash

        user.public_key = user_row.public_key
        user.private_key = serialization.load_pem_private_key(
            user_row.private_key, password=None
        )
        return user

    if not user_row:
        print("No user found with the provided username and password.")
        return None

    return None


def get_all_users_except_current(username):
    session = Session()

    user_row = session.query(UserModel).filter(UserModel.username != username).all()

    session.close()

    if user_row:
        return user_row

    return None


def get_keys_by_username(username):
    session = Session()

    user_row = session.query(UserModel).filter_by(username=username).first()

    session.close()

    if user_row:
        return user_row.private_key, user_row.public_key

    return None


def change_password(username):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    user_row = session.query(UserModel).filter_by(username=username).first()

    if not user_row:
        print("Wrong username")
        session.close()  # Close session if username is incorrect
        return False

    old_password = inquirer.secret(
        message="Old password:",
        transformer=lambda _: "[hidden]",
        validate=lambda text: compute_hash(text) == user_row.password_hash,
        invalid_message="Wrong password",
    ).execute()

    password_hash = compute_hash(old_password)

    if password_hash != user_row.password_hash:
        print("Wrong password")
        session.close()  # Close session if password is incorrect
        return False

    new_password = inquirer.secret(
        message="New password:",
        validate=PasswordValidator(),
        transformer=lambda _: "[hidden]",
    ).execute()
    new_password_hash = compute_hash(new_password)

    confirm = inquirer.confirm(message="Confirm?", default=True).execute()

    if confirm:
        user_row.password_hash = new_password_hash
        session.add(user_row)  # This is necessary to ensure changes are tracked
        session.commit()  # Commit changes to the database
        session.close()  # Close the session
        Request.broadcast_update_password(user_row)
        return True
    else:
        session.close()
        return False


def delete_account(username):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    try:
        user_row = session.query(UserModel).filter_by(username=username).first()

        if not user_row:
            print("Account with the provided username does not exist.")
            return False

        # Ask for password confirmation before deleting the account
        password = inquirer.secret(
            message="Enter your password to confirm account deletion:",
            invalid_message="Wrong password",
        ).execute()

        password_hash = compute_hash(password)

        if password_hash != user_row.password_hash:
            print("Wrong password. Account deletion aborted.")
            return False

        confirm = inquirer.confirm(
            message="Are you sure? Account deletion is irreversible!", default=False
        ).execute()

        if confirm:
            session.delete(user_row)
            session.commit()
            session.close()
            Request.broadcast_delete_user(user_row)
            return True
        else:
            session.close()
            return False

    except Exception as e:
        print(f"Error deleting account: {e}")
        session.rollback()
        return False

    finally:
        session.close()


def update_password(user):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    try:
        user_row = session.query(UserModel).filter_by(username=user.username).first()

        if not user_row:
            print("Account with the provided username does not exist.")
            return False

        user_row.password_hash = user.password_hash
        session.add(user_row)
        session.commit()
        session.close()
        return True

    except Exception as e:
        print(f"Error updating password: {e}")
        session.rollback()
        return False

    finally:
        session.close()


def delete_user(user_data):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    try:
        user_row = session.query(UserModel).filter_by(username=user_data.username).first()

        if not user_row:
            print("Account with the provided username does not exist.")
            return False

        session.delete(user_row)
        session.commit()
        session.close()
        return True

    except Exception as e:
        print(f"Error deleting user: {e}")
        session.rollback()
        return False

    finally:
        session.close()

def delete_database():
    engine.dispose()

    if os.path.exists("goodchain.db"):
        try:
            os.remove("goodchain.db")
            print("Database deleted successfully.")
        except PermissionError:
            print(
                "Failed to delete the database. Ensure all connections are closed and try again."
            )
    else:
        print("Database not found.")
