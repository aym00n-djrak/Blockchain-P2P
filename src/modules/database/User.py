from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    private_key = Column(LargeBinary, nullable=False)
    is_logged_in = Column(Boolean, default=False)

    def login(self, user_instance):
        self.username = user_instance.username
        self.private_key = user_instance.private_key
        self.public_key = user_instance.public_key
        self.password_hash = user_instance.password_hash
        self.is_logged_in = True

    def logout(self):
        self.username = None
        self.private_key = None
        self.public_key = None
        self.password_hash = None
        self.is_logged_in = False

