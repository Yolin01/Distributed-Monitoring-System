from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True

class NodeBase(BaseModel):
    external_id: str
    name: Optional[str] = None

class NodeCreate(NodeBase):
    pass

class NodeResponse(NodeBase):
    id: int
    status: str
    registered_at: datetime
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True

class MetricBase(BaseModel):
    node_id: int
    cpu_percent: float
    memory_percent: float
    disk_percent: float

class MetricCreate(MetricBase):
    timestamp: datetime

class MetricResponse(MetricBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    node_id: int
    metric_type: str
    threshold: float
    actual_value: float
    severity: str
    message: str

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    acknowledged: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None