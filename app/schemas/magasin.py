from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MagasinBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    adresse: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    is_principal: bool = True


class MagasinCreate(MagasinBase):
    pass


class MagasinUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    adresse: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    is_principal: Optional[bool] = None


class MagasinResponse(MagasinBase):
    id: str
    entreprise_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
