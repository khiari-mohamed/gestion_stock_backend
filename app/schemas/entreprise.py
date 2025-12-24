from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EntrepriseBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    matricule_fiscal: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    devise_principale: str = "TND"
    devise_secondaire: Optional[str] = None


class EntrepriseCreate(EntrepriseBase):
    pass


class EntrepriseUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    devise_secondaire: Optional[str] = None


class EntrepriseResponse(EntrepriseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
