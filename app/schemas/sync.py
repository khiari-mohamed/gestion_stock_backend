from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class MouvementSync(BaseModel):
    type: str
    article_id: str
    magasin_id: str
    quantite: int
    prix_unitaire: Optional[float] = None
    motif: Optional[str] = None
    date_mouvement: datetime

class VenteSync(BaseModel):
    article_id: str
    magasin_id: str
    quantite: int
    prix_unitaire: float
    date_vente: datetime

class ArticleSync(BaseModel):
    id: str
    data: Dict[str, Any]

class SyncRequest(BaseModel):
    mouvements: Optional[List[MouvementSync]] = []
    ventes: Optional[List[VenteSync]] = []
    articles: Optional[List[ArticleSync]] = []

class SyncResponse(BaseModel):
    success: bool
    mouvements_synced: int
    articles_synced: int
    ventes_synced: int
    errors: List[str]
    timestamp: datetime
