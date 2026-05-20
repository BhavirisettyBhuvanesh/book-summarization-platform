from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Connects the user to their past queries
    history = relationship("QueryHistory", back_populates="owner")

class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(Text)
    pipeline_used = Column(String)
    
    # We store the scores (F, R, D) as a JSON string
    scores_json = Column(Text) 
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Connects this query to a specific user
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="history")
