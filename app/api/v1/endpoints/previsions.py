from fastapi import APIRouter, Depends, Query
from typing import List
from app.api.v1.models.schemas import PrevisionResponse
from app.services.ai_service import AIService
from app.core.security import get_current_user

router = APIRouter()

@router.get("/article/{article_id}", response_model=List[PrevisionResponse])
async def get_previsions_by_article(
    article_id: str,
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les prévisions pour un article (Phase 2)"""
    # TODO: Implémenter en Phase 2
    return []

@router.post("/calculate/{magasin_id}", status_code=202)
async def trigger_prevision_calculation(
    magasin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Déclencher le calcul des prévisions pour un magasin (Phase 2)"""
    # TODO: Implémenter en Phase 2
    return {"message": "Calcul des prévisions lancé (Phase 2)"}
