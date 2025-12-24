from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from app.api.v1.models.schemas import FournisseurCreate, FournisseurUpdate, FournisseurResponse
from app.services.fournisseur_service import FournisseurService
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=FournisseurResponse, status_code=201)
async def create_fournisseur(
    data: FournisseurCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau fournisseur"""
    try:
        fournisseur = await FournisseurService.create_fournisseur(data)
        return fournisseur
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{fournisseur_id}", response_model=FournisseurResponse)
async def get_fournisseur(
    fournisseur_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un fournisseur par ID"""
    fournisseur = await FournisseurService.get_fournisseur(fournisseur_id)
    if not fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return fournisseur

@router.get("/entreprise/{entreprise_id}", response_model=List[FournisseurResponse])
async def get_fournisseurs_by_entreprise(
    entreprise_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """Lister tous les fournisseurs d'une entreprise"""
    fournisseurs = await FournisseurService.get_fournisseurs_by_entreprise(entreprise_id, skip, limit)
    return fournisseurs

@router.put("/{fournisseur_id}", response_model=FournisseurResponse)
async def update_fournisseur(
    fournisseur_id: str,
    data: FournisseurUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un fournisseur"""
    fournisseur = await FournisseurService.update_fournisseur(fournisseur_id, data)
    if not fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
    return fournisseur

@router.delete("/{fournisseur_id}", status_code=204)
async def delete_fournisseur(
    fournisseur_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un fournisseur"""
    await FournisseurService.delete_fournisseur(fournisseur_id)
    return None
