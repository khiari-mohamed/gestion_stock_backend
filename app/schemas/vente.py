from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class VenteBase(BaseModel):
    quantite: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., gt=0)

class VenteCreate(VenteBase):
    article_id: str
    magasin_id: str
    date_vente: datetime = Field(default_factory=datetime.now)

class VenteBulkCreate(BaseModel):
    ventes: List[VenteCreate]

class VenteResponse(VenteBase):
    id: str
    article_id: str
    magasin_id: str
    montant_total: float
    date_vente: datetime
    jour_semaine: int
    semaine_annee: int
    created_at: datetime

    class Config:
        from_attributes = True
