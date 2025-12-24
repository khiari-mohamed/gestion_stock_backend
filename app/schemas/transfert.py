from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransfertCreate(BaseModel):
    article_id: str
    magasin_origine_id: str
    magasin_destination_id: str
    quantite: int = Field(..., gt=0)
    notes: Optional[str] = None


class TransfertUpdate(BaseModel):
    statut: Optional[str] = None
    notes: Optional[str] = None


class TransfertResponse(BaseModel):
    id: str
    reference: str
    article_id: str
    magasin_origine_id: str
    magasin_destination_id: str
    quantite: int
    statut: str
    date_transfert: Optional[datetime] = None
    date_reception: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
