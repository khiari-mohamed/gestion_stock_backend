from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.bon_commande import BonCommandeCreate, BonCommandeResponse
from app.core.database import get_db
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(prefix="/bons-commande", tags=["Bons de Commande"])


@router.post("/", response_model=BonCommandeResponse)
async def create_bon_commande(
    bon: BonCommandeCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Créer un bon de commande"""
    count = await db.boncommande.count()
    reference = f"BC-{datetime.now().year}-{count + 1:04d}"
    
    montant_total = sum(ligne.quantite_commandee * ligne.prix_unitaire for ligne in bon.lignes)
    
    new_bon = await db.boncommande.create(
        data={
            "reference": reference,
            "entreprise_id": current_user.entreprise_id,
            "fournisseur_id": bon.fournisseur_id,
            "statut": "BROUILLON",
            "montant_total": montant_total,
            "notes": bon.notes,
            "lignes": {
                "create": [
                    {
                        "article_id": ligne.article_id,
                        "quantite_commandee": ligne.quantite_commandee,
                        "prix_unitaire": ligne.prix_unitaire,
                        "montant_total": ligne.quantite_commandee * ligne.prix_unitaire
                    }
                    for ligne in bon.lignes
                ]
            }
        },
        include={"lignes": True, "fournisseur": True}
    )
    return new_bon


@router.get("/", response_model=List[BonCommandeResponse])
async def list_bons_commande(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lister les bons de commande"""
    bons = await db.boncommande.find_many(
        where={"entreprise_id": current_user.entreprise_id},
        include={"lignes": True, "fournisseur": True}
    )
    return bons


@router.patch("/{bon_id}/confirmer")
async def confirmer_bon_commande(
    bon_id: str,
    date_livraison_prevue: datetime,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Confirmer un bon de commande"""
    bon = await db.boncommande.find_unique(where={"id": bon_id})
    if not bon or bon.entreprise_id != current_user.entreprise_id:
        raise HTTPException(status_code=404, detail="Bon de commande non trouvé")
    
    updated = await db.boncommande.update(
        where={"id": bon_id},
        data={
            "statut": "CONFIRMEE",
            "date_commande": datetime.now(),
            "date_livraison_prevue": date_livraison_prevue
        }
    )
    return updated
