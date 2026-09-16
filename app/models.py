from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base
from datetime import datetime, timezone
import hashlib

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False)


class ReportJob(Base):
    __tablename__ = "report_jobs"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending")  # pending, running, done, failed
    file_path = Column(String, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class EnrichmentJob(Base):
    __tablename__ = "enrichment_jobs"
    id = Column(Integer, primary_key=True, index=True)
    input_hash = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, running, done, failed
    input_data = Column(Text)
    result = Column(Text, nullable=True)
    error = Column(String, nullable=True)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)