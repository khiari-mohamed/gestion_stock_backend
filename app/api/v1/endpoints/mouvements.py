from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from app.api.v1.models.schemas import MouvementStockCreate, MouvementStockResponse
from app.services.mouvement_service import MouvementService
from app.core.security import get_current_user, verify_user_access_to_magasin, verify_user_access_to_article
from app.core.rbac import Permission, check_permission
from app.core.database import prisma
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=MouvementStockResponse, status_code=201)
async def create_mouvement(
    data: MouvementStockCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_MOUVEMENT))
):
    """Créer un nouveau mouvement de stock (entrée/sortie/ajustement/retour)"""
    try:
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, data.magasin_id):
            logger.warning(
                f"Unauthorized mouvement creation attempt for magasin {data.magasin_id} "
                f"by user {current_user.get('id')} from enterprise {current_user.get('entreprise_id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        # Verify article belongs to the warehouse
        if not await verify_user_access_to_article(current_user, data.article_id):
            logger.warning(
                f"Unauthorized mouvement for article {data.article_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Article non trouvé ou vous n'avez pas accès à cet article"
            )
        
        mouvement = await MouvementService.create_mouvement(data)
        
        logger.info(
            f"Mouvement créé: {mouvement.get('id')} "
            f"article={data.article_id} magasin={data.magasin_id} "
            f"user={current_user.get('id')}"
        )
        
        return mouvement
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating mouvement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/article/{article_id}", response_model=List[MouvementStockResponse])
async def get_mouvements_by_article(
    article_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(check_permission(Permission.READ_MOUVEMENT))
):
    """Récupérer l'historique des mouvements d'un article"""
    try:
        # Verify user has access to the article
        if not await verify_user_access_to_article(current_user, article_id):
            logger.warning(
                f"Unauthorized mouvement read for article {article_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Article non trouvé ou vous n'avez pas accès à cet article"
            )
        
        mouvements = await MouvementService.get_mouvements_by_article(article_id, limit)
        
        logger.info(
            f"Mouvements retrieved for article {article_id} "
            f"user={current_user.get('id')} count={len(mouvements)}"
        )
        
        return mouvements
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mouvements by article: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/magasin/{magasin_id}", response_model=List[MouvementStockResponse])
async def get_mouvements_by_magasin(
    magasin_id: str,
    date_debut: Optional[datetime] = None,
    date_fin: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(check_permission(Permission.READ_MOUVEMENT))
):
    """Récupérer tous les mouvements d'un magasin avec filtres optionnels"""
    try:
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, magasin_id):
            logger.warning(
                f"Unauthorized mouvement read for magasin {magasin_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        mouvements = await MouvementService.get_mouvements_by_magasin(
            magasin_id, date_debut, date_fin, skip, limit
        )
        
        logger.info(
            f"Mouvements retrieved for magasin {magasin_id} "
            f"user={current_user.get('id')} count={len(mouvements)} "
            f"period={date_debut} to {date_fin}"
        )
        
        return mouvements
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mouvements by magasin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{mouvement_id}", response_model=MouvementStockResponse)
async def get_mouvement(
    mouvement_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_MOUVEMENT))
):
    """Récupérer les détails d'un mouvement spécifique"""
    try:
        mouvement = await prisma.mouvement_stock.find_unique(
            where={"id": mouvement_id},
            include={"article": True, "magasin": True}
        )
        
        if not mouvement:
            raise HTTPException(status_code=404, detail="Mouvement non trouvé")
        
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, mouvement.magasin_id):
            logger.warning(
                f"Unauthorized mouvement access {mouvement_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce mouvement"
            )
        
        logger.info(f"Mouvement retrieved: {mouvement_id} user={current_user.get('id')}")
        
        return mouvement
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mouvement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{mouvement_id}", response_model=MouvementStockResponse)
async def update_mouvement(
    mouvement_id: str,
    data: MouvementStockCreate,
    current_user: dict = Depends(check_permission(Permission.UPDATE_MOUVEMENT))
):
    """Mettre à jour un mouvement (seulement si pas encore validé)"""
    try:
        mouvement = await prisma.mouvement_stock.find_unique(
            where={"id": mouvement_id},
            include={"magasin": True}
        )
        
        if not mouvement:
            raise HTTPException(status_code=404, detail="Mouvement non trouvé")
        
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, mouvement.magasin_id):
            logger.warning(
                f"Unauthorized mouvement update {mouvement_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce mouvement"
            )
        
        # Check if mouvement is already validated (only PATRON/GERANT can update)
        if mouvement.statut == "VALIDÉ":
            if current_user.get('role') not in ['PATRON', 'GERANT']:
                logger.warning(
                    f"Attempt to update validated mouvement {mouvement_id} "
                    f"by {current_user.get('role')} user"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Vous ne pouvez pas modifier un mouvement validé"
                )
        
        updated = await prisma.mouvement_stock.update(
            where={"id": mouvement_id},
            data={
                "article_id": data.article_id,
                "magasin_id": data.magasin_id,
                "type_mouvement": data.type_mouvement,
                "quantite": data.quantite,
                "prix_unitaire": data.prix_unitaire,
                "commentaire": data.commentaire
            },
            include={"article": True, "magasin": True}
        )
        
        logger.info(
            f"Mouvement updated: {mouvement_id} "
            f"user={current_user.get('id')} role={current_user.get('role')}"
        )
        
        return updated
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mouvement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{mouvement_id}", status_code=204)
async def delete_mouvement(
    mouvement_id: str,
    current_user: dict = Depends(check_permission(Permission.DELETE_MOUVEMENT))
):
    """Supprimer un mouvement (seulement PATRON et GERANT)"""
    try:
        # Role check - deletion is restricted
        if current_user.get('role') not in ['PATRON', 'GERANT']:
            logger.warning(
                f"Unauthorized mouvement deletion {mouvement_id} "
                f"by {current_user.get('role')} user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Seul un administrateur peut supprimer les mouvements"
            )
        
        mouvement = await prisma.mouvement_stock.find_unique(
            where={"id": mouvement_id},
            include={"magasin": True}
        )
        
        if not mouvement:
            raise HTTPException(status_code=404, detail="Mouvement non trouvé")
        
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, mouvement.magasin_id):
            logger.warning(
                f"Unauthorized mouvement deletion {mouvement_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce mouvement"
            )
        
        await prisma.mouvement_stock.delete(where={"id": mouvement_id})
        
        logger.info(
            f"Mouvement deleted: {mouvement_id} "
            f"user={current_user.get('id')} role={current_user.get('role')}"
        )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mouvement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
