from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.magasin import MagasinCreate, MagasinUpdate, MagasinResponse
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/magasins", tags=["Magasins"])


@router.post("/", response_model=MagasinResponse)
async def create_magasin(
    magasin: MagasinCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Créer un nouveau magasin"""
    new_magasin = await db.magasin.create(
        data={
            "nom": magasin.nom,
            "code": magasin.code,
            "adresse": magasin.adresse,
            "ville": magasin.ville,
            "telephone": magasin.telephone,
            "is_principal": magasin.is_principal,
            "entreprise_id": current_user.entreprise_id
        }
    )
    return new_magasin


@router.get("/", response_model=List[MagasinResponse])
async def list_magasins(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lister tous les magasins de l'entreprise"""
    magasins = await db.magasin.find_many(
        where={"entreprise_id": current_user.entreprise_id}
    )
    return magasins


@router.get("/{magasin_id}", response_model=MagasinResponse)
async def get_magasin(
    magasin_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Récupérer un magasin par ID"""
    magasin = await db.magasin.find_unique(where={"id": magasin_id})
    if not magasin or magasin.entreprise_id != current_user.entreprise_id:
        raise HTTPException(status_code=404, detail="Magasin non trouvé")
    return magasin


@router.put("/{magasin_id}", response_model=MagasinResponse)
async def update_magasin(
    magasin_id: str,
    magasin: MagasinUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Mettre à jour un magasin"""
    existing = await db.magasin.find_unique(where={"id": magasin_id})
    if not existing or existing.entreprise_id != current_user.entreprise_id:
        raise HTTPException(status_code=404, detail="Magasin non trouvé")
    
    updated = await db.magasin.update(
        where={"id": magasin_id},
        data=magasin.dict(exclude_unset=True)
    )
    return updated


@router.delete("/{magasin_id}")
async def delete_magasin(
    magasin_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Supprimer un magasin"""
    existing = await db.magasin.find_unique(where={"id": magasin_id})
    if not existing or existing.entreprise_id != current_user.entreprise_id:
        raise HTTPException(status_code=404, detail="Magasin non trouvé")
    
    await db.magasin.delete(where={"id": magasin_id})
    return {"message": "Magasin supprimé avec succès"}
