from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from app.api.v1.models.schemas import MouvementStockCreate, MouvementStockResponse
from app.services.mouvement_service import MouvementService
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=MouvementStockResponse, status_code=201)
async def create_mouvement(
    data: MouvementStockCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau mouvement de stock (entrée/sortie/ajustement/retour)"""
    try:
        mouvement = await MouvementService.create_mouvement(data)
        return mouvement
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/article/{article_id}", response_model=List[MouvementStockResponse])
async def get_mouvements_by_article(
    article_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer l'historique des mouvements d'un article"""
    mouvements = await MouvementService.get_mouvements_by_article(article_id, limit)
    return mouvements

@router.get("/magasin/{magasin_id}", response_model=List[MouvementStockResponse])
async def get_mouvements_by_magasin(
    magasin_id: str,
    date_debut: Optional[datetime] = None,
    date_fin: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer tous les mouvements d'un magasin avec filtres optionnels"""
    mouvements = await MouvementService.get_mouvements_by_magasin(
        magasin_id, date_debut, date_fin, skip, limit
    )
    return mouvements
