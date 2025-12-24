from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FournisseurBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    type: str = "FORMEL"
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    matricule_fiscal: Optional[str] = None
    delai_livraison: Optional[int] = None
    notes: Optional[str] = None


class FournisseurCreate(FournisseurBase):
    pass


class FournisseurUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    matricule_fiscal: Optional[str] = None
    delai_livraison: Optional[int] = None
    notes: Optional[str] = None


class FournisseurResponse(FournisseurBase):
    id: str
    entreprise_id: str
    score_fiabilite: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
