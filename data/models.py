from sqlalchemy import Integer, String, Boolean, Column, ForeignKey
from database import Base

class AuthenticatedUsers(Base):
    __tablename__ = "authenticated_users"


    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    email = Column(String)
    password = Column(String)
