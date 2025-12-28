from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.utils.validators import validate_phone_tunisie, validate_matricule_fiscal

class UserBase(BaseModel):
    email: EmailStr
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    telephone: Optional[str] = None
    langue: str = Field(default="fr", pattern="^(fr|ar)$")
    role: str = Field(default="employe", pattern="^(patron|employe|comptable)$")
    
    @field_validator('telephone')
    @classmethod
    def validate_phone(cls, v):
        if v and not validate_phone_tunisie(v):
            raise ValueError('Numéro de téléphone tunisien invalide')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    entreprise_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    entreprise_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
