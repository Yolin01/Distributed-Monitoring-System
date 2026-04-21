from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)

    #  ID métier (celui envoyé par l'agent)
    external_id = Column(String, unique=True, index=True, nullable=False)

    name = Column(String)
    status = Column(String, default="active")

    registered_at = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, onupdate=func.now())

    # relation
    metrics = relationship("Metric", back_populates="node", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)

    # FK vers Node.id
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)

    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)

    # relation
    node = relationship("Node", back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    node_id = Column(Integer, ForeignKey("nodes.id"))

    metric_type = Column(String)
    threshold = Column(Float)
    actual_value = Column(Float)
    severity = Column(String)

    message = Column(String)

    created_at = Column(DateTime, server_default=func.now())
    acknowledged = Column(Boolean, default=False)

    node = relationship("Node")