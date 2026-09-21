from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserState(Base):
    __tablename__ = "user_states"

    user_id = Column(String(64), primary_key=True)
    state = Column(String(128), nullable=True)
    data = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String(64), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    place_type = Column(String(64), nullable=True)
    promo_text = Column(Text, nullable=True)
    schedule = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    map_url = Column(String(512), nullable=True)
    discount_info = Column(String(255), default="*Скидки и льготы предоставляются при предоставлении оригинала подтверждающего документа.")

    favorites = relationship("UserFavorite", back_populates="place", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String(64), primary_key=True)
    city = Column(String(64), nullable=False)
    category = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (UniqueConstraint("user_id", "place_id", name="unique_user_place"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    place = relationship("Place", back_populates="favorites")
