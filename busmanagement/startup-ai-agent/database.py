from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration PostgreSQL (ou SQLite pour dev)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./startup_agent.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle SQLAlchemy pour la persistance
class StartupDB(Base):
    __tablename__ = "startups"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    profile = Column(Text)  # JSON string
    generated_plan = Column(Text, nullable=True)  # JSON string
    matched_investors = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime)
    last_activity = Column(DateTime)

# Créer les tables
Base.metadata.create_all(bind=engine)