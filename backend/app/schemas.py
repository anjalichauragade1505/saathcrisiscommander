from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InjectEventRequest(BaseModel):
    type: str  # flood | earthquake | road_block | road_clear | communication_failure | connectivity_restored
    rainfall_mm: Optional[float] = None
    epicenter_zone_id: Optional[int] = None
    magnitude: Optional[float] = None
    road_id: Optional[int] = None
    zone_id: Optional[int] = None


class NotificationRespondRequest(BaseModel):
    approve: bool


class FieldReportRequest(BaseModel):
    zone_id: int
    message: str
    client_timestamp: Optional[datetime] = None


class FieldReportItem(BaseModel):
    message: str
    client_timestamp: datetime


class FieldSyncRequest(BaseModel):
    zone_id: int
    reports: list[FieldReportItem]
