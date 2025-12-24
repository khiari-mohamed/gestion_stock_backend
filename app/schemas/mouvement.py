from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MouvementStockBase(BaseModel):
    type: str = Field(..., pattern="^(entree|sortie|ajustement|retour)$")
    quantite: int = Field(..., gt=0)
    prix_unitaire: Optional[float] = Field(None, ge=0)
    motif: Optional[str] = None
    reference_doc: Optional[str] = None
    date_mouvement: Optional[datetime] = None

class MouvementStockCreate(MouvementStockBase):
    article_id: str
    magasin_id: str
    fournisseur_id: Optional[str] = None

class MouvementStockResponse(MouvementStockBase):
    id: str
    article_id: str
    magasin_id: str
    fournisseur_id: Optional[str]
    photo_doc_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
