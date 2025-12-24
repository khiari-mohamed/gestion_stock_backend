from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.transfert import TransfertCreate, TransfertResponse, TransfertUpdate
from app.core.database import get_db
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(prefix="/transferts", tags=["Transferts"])


@router.post("/", response_model=TransfertResponse)
async def create_transfert(
    transfert: TransfertCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Créer un transfert entre magasins"""
    # Générer référence unique
    count = await db.transfertstock.count()
    reference = f"TRF-{datetime.now().year}-{count + 1:04d}"
    
    new_transfert = await db.transfertstock.create(
        data={
            "reference": reference,
            "article_id": transfert.article_id,
            "magasin_origine_id": transfert.magasin_origine_id,
            "magasin_destination_id": transfert.magasin_destination_id,
            "quantite": transfert.quantite,
            "notes": transfert.notes,
            "statut": "EN_ATTENTE"
        }
    )
    return new_transfert


@router.get("/", response_model=List[TransfertResponse])
async def list_transferts(
    magasin_id: str = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lister les transferts"""
    where = {}
    if magasin_id:
        where = {
            "OR": [
                {"magasin_origine_id": magasin_id},
                {"magasin_destination_id": magasin_id}
            ]
        }
    
    transferts = await db.transfertstock.find_many(
        where=where,
        include={"article": True, "magasin_origine": True, "magasin_destination": True}
    )
    return transferts


@router.patch("/{transfert_id}/confirmer")
async def confirmer_transfert(
    transfert_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Confirmer l'envoi d'un transfert"""
    transfert = await db.transfertstock.find_unique(where={"id": transfert_id})
    if not transfert:
        raise HTTPException(status_code=404, detail="Transfert non trouvé")
    
    # Déduire du stock origine
    await db.article.update(
        where={"id": transfert.article_id, "magasin_id": transfert.magasin_origine_id},
        data={"stock_actuel": {"decrement": transfert.quantite}}
    )
    
    updated = await db.transfertstock.update(
        where={"id": transfert_id},
        data={"statut": "EN_COURS", "date_transfert": datetime.now()}
    )
    return updated


@router.patch("/{transfert_id}/recevoir")
async def recevoir_transfert(
    transfert_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Confirmer la réception d'un transfert"""
    transfert = await db.transfertstock.find_unique(where={"id": transfert_id})
    if not transfert:
        raise HTTPException(status_code=404, detail="Transfert non trouvé")
    
    # Ajouter au stock destination
    await db.article.update(
        where={"id": transfert.article_id, "magasin_id": transfert.magasin_destination_id},
        data={"stock_actuel": {"increment": transfert.quantite}}
    )
    
    updated = await db.transfertstock.update(
        where={"id": transfert_id},
        data={"statut": "RECU", "date_reception": datetime.now()}
    )
    return updated
