from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.bon_commande import BonCommandeCreate, BonCommandeResponse
from app.core.database import prisma
from app.core.security import get_current_user
from app.core.rbac import Permission, check_permission
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bons-commande", tags=["Bons de Commande"])


@router.post("/", response_model=BonCommandeResponse)
async def create_bon_commande(
    bon: BonCommandeCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_BON_COMMANDE))
):
    """Créer un bon de commande"""
    try:
        # Verify user belongs to the enterprise
        fournisseur = await prisma.fournisseur.find_unique(
            where={"id": bon.fournisseur_id}
        )
        
        if not fournisseur or fournisseur.entreprise_id != current_user.get("entreprise_id"):
            logger.warning(
                f"Unauthorized bon_commande creation for fournisseur {bon.fournisseur_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce fournisseur"
            )
        
        count = await prisma.boncommande.count()
        reference = f"BC-{datetime.now().year}-{count + 1:04d}"
        
        montant_total = sum(
            ligne.quantite_commandee * ligne.prix_unitaire 
            for ligne in bon.lignes
        )
        
        new_bon = await prisma.boncommande.create(
            data={
                "reference": reference,
                "entreprise_id": current_user.get("entreprise_id"),
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
        
        logger.info(
            f"Bon de commande created: {new_bon.id} reference={reference} "
            f"fournisseur={bon.fournisseur_id} user={current_user.get('id')}"
        )
        
        return new_bon
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bon_commande: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[BonCommandeResponse])
async def list_bons_commande(
    current_user: dict = Depends(check_permission(Permission.READ_BON_COMMANDE))
):
    """Lister les bons de commande"""
    try:
        bons = await prisma.boncommande.find_many(
            where={"entreprise_id": current_user.get("entreprise_id")},
            include={"lignes": True, "fournisseur": True}
        )
        
        logger.info(
            f"Bons de commande list retrieved for enterprise {current_user.get('entreprise_id')} "
            f"user={current_user.get('id')} count={len(bons)}"
        )
        
        return bons
    
    except Exception as e:
        logger.error(f"Error retrieving bons_commande: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{bon_id}", response_model=BonCommandeResponse)
async def get_bon_commande(
    bon_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_BON_COMMANDE))
):
    """Récupérer un bon de commande spécifique"""
    try:
        bon = await prisma.boncommande.find_unique(
            where={"id": bon_id},
            include={"lignes": True, "fournisseur": True}
        )
        
        if not bon:
            raise HTTPException(status_code=404, detail="Bon de commande non trouvé")
        
        # Verify user has access
        if bon.entreprise_id != current_user.get("entreprise_id"):
            logger.warning(
                f"Unauthorized bon_commande access {bon_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce bon de commande"
            )
        
        logger.info(f"Bon de commande retrieved: {bon_id} user={current_user.get('id')}")
        
        return bon
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bon_commande: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{bon_id}/confirmer")
async def confirmer_bon_commande(
    bon_id: str,
    date_livraison_prevue: datetime,
    current_user: dict = Depends(check_permission(Permission.UPDATE_BON_COMMANDE))
):
    """Confirmer un bon de commande (GERANT/PATRON only)"""
    try:
        # Role check
        if current_user.get('role') not in ['PATRON', 'GERANT']:
            logger.warning(
                f"Unauthorized bon_commande confirmation {bon_id} "
                f"by {current_user.get('role')} user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Seul un administrateur peut confirmer les bons de commande"
            )
        
        bon = await prisma.boncommande.find_unique(where={"id": bon_id})
        
        if not bon:
            raise HTTPException(status_code=404, detail="Bon de commande non trouvé")
        
        # Verify user has access
        if bon.entreprise_id != current_user.get("entreprise_id"):
            logger.warning(
                f"Unauthorized bon_commande confirmation {bon_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce bon de commande"
            )
        
        updated = await prisma.boncommande.update(
            where={"id": bon_id},
            data={
                "statut": "CONFIRMEE",
                "date_commande": datetime.now(),
                "date_livraison_prevue": date_livraison_prevue
            },
            include={"lignes": True, "fournisseur": True}
        )
        
        logger.info(
            f"Bon de commande confirmed: {bon_id} "
            f"user={current_user.get('id')} role={current_user.get('role')}"
        )
        
        return updated
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming bon_commande: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
