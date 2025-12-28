from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.utils.validators import validate_phone_tunisie, validate_matricule_fiscal


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
    
    @field_validator('telephone')
    @classmethod
    def validate_phone(cls, v):
        if v and not validate_phone_tunisie(v):
            raise ValueError('Numéro de téléphone tunisien invalide')
        return v
    
    @field_validator('matricule_fiscal')
    @classmethod
    def validate_matricule(cls, v):
        if v and not validate_matricule_fiscal(v):
            raise ValueError('Matricule fiscal tunisien invalide (format: 1234567A)')
        return v


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
