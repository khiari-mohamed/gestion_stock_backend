from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    type: str
    titre: str
    message: str
    canal: str
    statut: str
    destinaire: Optional[str] = None
    date_envoi: Optional[datetime] = None
    date_reception: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
