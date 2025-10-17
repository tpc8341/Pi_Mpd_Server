from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    settings = Column(String)

    playlists = relationship("UserPlaylist", back_populates="owner")
    bulletins = relationship("Bulletin", back_populates="owner")

class UserPlaylist(Base):
    __tablename__ = "user_playlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    playlist_name = Column(String, index=True) # e.g., "pc_playlist"
    playlist_data = Column(String) # Storing as a JSON string for simplicity

    owner = relationship("User", back_populates="playlists")

class Bulletin(Base):
    __tablename__ = "bulletins"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    filename = Column(String)
    filepath = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="bulletins")
    