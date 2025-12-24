from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class PrevisionResponse(BaseModel):
    id: str
    article_id: str
    magasin_id: str
    date_calcul: datetime
    date_periode: datetime
    date_fin_periode: datetime
    quantite_prevue: float
    confiance: float
    algorithme: str
    version_modele: str
    metriques: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PrevisionSuggestion(BaseModel):
    article_id: str
    code: str
    designation: str
    stock_actuel: int
    demande_prevue: int
    quantite_a_commander: int
    confiance: float
    priorite: str
