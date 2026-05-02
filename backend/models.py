from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=True)  # nullable for Google OAuth users
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(120))
    reset_token = Column(String(100), nullable=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    stats = relationship("UserStats", back_populates="user", uselist=False)
    test_results = relationship("TestResult", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    bio = Column(Text)
    avatar_url = Column(Text)
    country = Column(String(2))
    keyboard_layout = Column(String(50), default="qwerty")
    theme_pref = Column(String(30), default="sketch")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wpm = Column(Numeric(6, 2), nullable=False)
    raw_wpm = Column(Numeric(6, 2), nullable=False)
    accuracy = Column(Numeric(5, 2), nullable=False)
    mode = Column(String(20), nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="test_results")

class UserStats(Base):
    __tablename__ = "user_stats"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    total_tests = Column(Integer, default=0)
    best_wpm = Column(Numeric(6, 2), default=0)
    avg_wpm = Column(Numeric(6, 2), default=0)
    avg_accuracy = Column(Numeric(5, 2), default=0)
    total_xp = Column(BigInteger, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="stats")
