from fastapi import APIRouter, Depends, Query
from app.services.peremption_service import PeremptionService
from app.core.security import get_current_user

router = APIRouter(prefix="/peremption", tags=["Péremption"])

@router.get("/check/{magasin_id}")
async def check_peremptions(
    magasin_id: str,
    jours_alerte: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Vérifier les articles proches de la péremption"""
    return await PeremptionService.check_peremptions(magasin_id, jours_alerte)

@router.get("/suggestions/{magasin_id}")
async def get_peremption_suggestions(
    magasin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtenir des suggestions d'actions pour les articles proches de péremption"""
    suggestions = await PeremptionService.suggest_actions(magasin_id)
    return {"suggestions": suggestions, "total": len(suggestions)}

@router.get("/fifo/{article_id}")
async def get_fifo_order(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtenir l'ordre FIFO pour un article"""
    return await PeremptionService.get_fifo_order(article_id)
