from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from app.schemas.vente import VenteCreate, VenteResponse, VenteBulkCreate
from app.services.vente_service import VenteService
from app.core.security import get_current_user, verify_user_access_to_magasin, verify_user_access_to_article
from app.core.rbac import Permission, check_permission
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ventes", tags=["Ventes"])


@router.post("/", response_model=VenteResponse, status_code=201)
async def create_vente(
    data: VenteCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_VENTE))
):
    """Enregistrer une vente"""
    try:
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, data.magasin_id):
            logger.warning(
                f"Unauthorized vente creation for magasin {data.magasin_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        # Verify article access
        if not await verify_user_access_to_article(current_user, data.article_id):
            logger.warning(
                f"Unauthorized vente for article {data.article_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Article non trouvé ou vous n'avez pas accès à cet article"
            )
        
        vente = await VenteService.create_vente(data)
        
        logger.info(
            f"Vente created: article={data.article_id} magasin={data.magasin_id} "
            f"quantite={data.quantite} user={current_user.get('id')}"
        )
        
        return vente
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vente: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk", status_code=201)
async def create_ventes_bulk(
    data: VenteBulkCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_VENTE))
):
    """Enregistrer plusieurs ventes en une fois (optimisé mobile)"""
    try:
        # Verify all ventes are for accessible warehouses
        for vente_data in data.ventes:
            if not await verify_user_access_to_magasin(current_user, vente_data.magasin_id):
                logger.warning(
                    f"Unauthorized bulk vente creation for magasin {vente_data.magasin_id} "
                    f"by user {current_user.get('id')}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Vous n'avez pas accès au magasin {vente_data.magasin_id}"
                )
            
            if not await verify_user_access_to_article(current_user, vente_data.article_id):
                logger.warning(
                    f"Unauthorized bulk vente for article {vente_data.article_id} "
                    f"by user {current_user.get('id')}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Article {vente_data.article_id} non accessible"
                )
        
        result = await VenteService.create_ventes_bulk(data.ventes)
        
        logger.info(
            f"Bulk ventes created: count={len(data.ventes)} "
            f"user={current_user.get('id')}"
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk ventes: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/article/{article_id}", response_model=List[VenteResponse])
async def get_ventes_by_article(
    article_id: str,
    date_debut: Optional[datetime] = None,
    date_fin: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(check_permission(Permission.READ_VENTE))
):
    """Historique des ventes d'un article"""
    try:
        # Verify user has access to the article
        if not await verify_user_access_to_article(current_user, article_id):
            logger.warning(
                f"Unauthorized vente history access for article {article_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Article non trouvé ou vous n'avez pas accès à cet article"
            )
        
        ventes = await VenteService.get_ventes_by_article(
            article_id, date_debut, date_fin, limit
        )
        
        logger.info(
            f"Ventes history retrieved for article {article_id} "
            f"user={current_user.get('id')} count={len(ventes)}"
        )
        
        return ventes
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ventes: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/magasin/{magasin_id}/stats")
async def get_ventes_stats(
    magasin_id: str,
    date_debut: Optional[datetime] = None,
    date_fin: Optional[datetime] = None,
    current_user: dict = Depends(check_permission(Permission.READ_VENTE))
):
    """Statistiques de ventes pour un magasin"""
    try:
        # Verify user has access to the warehouse
        if not await verify_user_access_to_magasin(current_user, magasin_id):
            logger.warning(
                f"Unauthorized vente stats access for magasin {magasin_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        stats = await VenteService.get_ventes_stats(
            magasin_id, date_debut, date_fin
        )
        
        logger.info(
            f"Ventes stats retrieved for magasin {magasin_id} "
            f"user={current_user.get('id')} period={date_debut} to {date_fin}"
        )
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ventes stats: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
