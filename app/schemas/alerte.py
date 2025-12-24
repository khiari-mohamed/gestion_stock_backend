from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlerteResponse(BaseModel):
    id: str
    type: str
    niveau: str
    message: str
    est_vue: bool
    est_resolue: bool
    date_alerte: datetime
    date_resolution: Optional[datetime] = None
    article_id: Optional[str] = None
    magasin_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlerteUpdate(BaseModel):
    est_vue: Optional[bool] = None
    est_resolue: Optional[bool] = None
