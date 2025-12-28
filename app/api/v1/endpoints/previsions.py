from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from app.api.v1.models.schemas import PrevisionResponse
from app.services.ai_forecast_service import AIForecastService
from app.core.security import get_current_user

router = APIRouter()

@router.get("/article/{article_id}", response_model=List[PrevisionResponse])
async def get_previsions_by_article(
    article_id: str,
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les prévisions pour un article"""
    ai_service = AIForecastService()
    previsions = await ai_service.get_previsions_by_article(article_id, limit)
    return previsions

@router.post("/calculate/{magasin_id}", status_code=202)
async def trigger_prevision_calculation(
    magasin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Déclencher le calcul des prévisions pour un magasin"""
    ai_service = AIForecastService()
    result = await ai_service.calculate_all_forecasts(magasin_id)
    return result

@router.get("/suggestions/{magasin_id}")
async def get_purchase_suggestions(
    magasin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtenir les suggestions de commande basées sur l'IA"""
    ai_service = AIForecastService()
    suggestions = await ai_service.get_purchase_suggestions(magasin_id)
    return {"suggestions": suggestions, "total": len(suggestions)}
