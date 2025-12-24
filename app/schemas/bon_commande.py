from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class LigneCommandeCreate(BaseModel):
    article_id: str
    quantite_commandee: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., gt=0)


class BonCommandeCreate(BaseModel):
    fournisseur_id: str
    lignes: List[LigneCommandeCreate]
    notes: Optional[str] = None


class LigneCommandeResponse(BaseModel):
    id: str
    article_id: str
    quantite_commandee: int
    quantite_recue: int
    prix_unitaire: float
    montant_total: float

    class Config:
        from_attributes = True


class BonCommandeResponse(BaseModel):
    id: str
    reference: str
    fournisseur_id: str
    statut: str
    montant_total: float
    date_commande: Optional[datetime] = None
    date_livraison_prevue: Optional[datetime] = None
    date_livraison_reelle: Optional[datetime] = None
    notes: Optional[str] = None
    lignes: List[LigneCommandeResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
