from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from app.api.v1.models.schemas import FournisseurCreate, FournisseurUpdate, FournisseurResponse
from app.services.fournisseur_service import FournisseurService
from app.services.fournisseur_scoring_service import FournisseurScoringService
from app.core.security import get_current_user
from app.core.rbac import Permission, check_permission
from app.core.database import prisma
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=FournisseurResponse, status_code=201)
async def create_fournisseur(
    data: FournisseurCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_FOURNISSEUR))
):
    """Créer un nouveau fournisseur"""
    try:
        # Verify user belongs to the enterprise
        if current_user.get('entreprise_id') != data.entreprise_id:
            logger.warning(
                f"Unauthorized fournisseur creation for enterprise {data.entreprise_id} "
                f"by user {current_user.get('id')} from {current_user.get('entreprise_id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à cette entreprise"
            )
        
        fournisseur = await FournisseurService.create_fournisseur(data)
        
        logger.info(
            f"Fournisseur created: {fournisseur.get('id')} "
            f"user={current_user.get('id')} enterprise={data.entreprise_id}"
        )
        
        return fournisseur
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating fournisseur: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{fournisseur_id}", response_model=FournisseurResponse)
async def get_fournisseur(
    fournisseur_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_FOURNISSEUR))
):
    """Récupérer un fournisseur par ID"""
    try:
        fournisseur = await FournisseurService.get_fournisseur(fournisseur_id)
        
        if not fournisseur:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        # Verify user has access to this fournisseur
        if fournisseur.get('entreprise_id') != current_user.get('entreprise_id'):
            logger.warning(
                f"Unauthorized fournisseur access {fournisseur_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce fournisseur"
            )
        
        logger.info(f"Fournisseur retrieved: {fournisseur_id} user={current_user.get('id')}")
        
        return fournisseur
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving fournisseur: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entreprise/{entreprise_id}", response_model=List[FournisseurResponse])
async def get_fournisseurs_by_entreprise(
    entreprise_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(check_permission(Permission.READ_FOURNISSEUR))
):
    """Lister tous les fournisseurs d'une entreprise"""
    try:
        # Verify user belongs to the enterprise
        if current_user.get('entreprise_id') != entreprise_id:
            logger.warning(
                f"Unauthorized fournisseur list for enterprise {entreprise_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à cette entreprise"
            )
        
        fournisseurs = await FournisseurService.get_fournisseurs_by_entreprise(
            entreprise_id, skip, limit
        )
        
        logger.info(
            f"Fournisseurs list retrieved for enterprise {entreprise_id} "
            f"user={current_user.get('id')} count={len(fournisseurs)}"
        )
        
        return fournisseurs
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving fournisseurs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{fournisseur_id}", response_model=FournisseurResponse)
async def update_fournisseur(
    fournisseur_id: str,
    data: FournisseurUpdate,
    current_user: dict = Depends(check_permission(Permission.UPDATE_FOURNISSEUR))
):
    """Mettre à jour un fournisseur"""
    try:
        fournisseur = await FournisseurService.get_fournisseur(fournisseur_id)
        
        if not fournisseur:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        # Verify user has access to this fournisseur
        if fournisseur.get('entreprise_id') != current_user.get('entreprise_id'):
            logger.warning(
                f"Unauthorized fournisseur update {fournisseur_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce fournisseur"
            )
        
        updated = await FournisseurService.update_fournisseur(fournisseur_id, data)
        
        logger.info(
            f"Fournisseur updated: {fournisseur_id} "
            f"user={current_user.get('id')}"
        )
        
        return updated
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating fournisseur: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{fournisseur_id}", status_code=204)
async def delete_fournisseur(
    fournisseur_id: str,
    current_user: dict = Depends(check_permission(Permission.DELETE_FOURNISSEUR))
):
    """Supprimer un fournisseur (seulement PATRON et GERANT)"""
    try:
        # Role check - deletion is restricted
        if current_user.get('role') not in ['PATRON', 'GERANT']:
            logger.warning(
                f"Unauthorized fournisseur deletion {fournisseur_id} "
                f"by {current_user.get('role')} user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Seul un administrateur peut supprimer les fournisseurs"
            )
        
        fournisseur = await FournisseurService.get_fournisseur(fournisseur_id)
        
        if not fournisseur:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        # Verify user has access to this fournisseur
        if fournisseur.get('entreprise_id') != current_user.get('entreprise_id'):
            logger.warning(
                f"Unauthorized fournisseur deletion {fournisseur_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce fournisseur"
            )
        
        await FournisseurService.delete_fournisseur(fournisseur_id)
        
        logger.info(
            f"Fournisseur deleted: {fournisseur_id} "
            f"user={current_user.get('id')} role={current_user.get('role')}"
        )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting fournisseur: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{fournisseur_id}/calculate-score")
async def calculate_fournisseur_score(
    fournisseur_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_FOURNISSEUR))
):
    """Calculer le score de fiabilité d'un fournisseur"""
    try:
        fournisseur = await FournisseurService.get_fournisseur(fournisseur_id)
        
        if not fournisseur:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        
        # Verify user has access to this fournisseur
        if fournisseur.get('entreprise_id') != current_user.get('entreprise_id'):
            logger.warning(
                f"Unauthorized score calculation for fournisseur {fournisseur_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce fournisseur"
            )
        
        score = await FournisseurScoringService.calculate_score(fournisseur_id)
        await FournisseurService.update_score(fournisseur_id, score)
        
        logger.info(
            f"Fournisseur score calculated: {fournisseur_id} "
            f"score={score} user={current_user.get('id')}"
        )
        
        return {"fournisseur_id": fournisseur_id, "score": score}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating fournisseur score: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/article/{article_id}/best-price")
async def get_best_price_for_article(
    article_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_FOURNISSEUR))
):
    """Trouver le meilleur prix pour un article"""
    try:
        # Verify user has access to the article
        article = await prisma.article.find_unique(
            where={"id": article_id},
            include={"magasin": True}
        )
        
        if not article:
            raise HTTPException(status_code=404, detail="Article non trouvé")
        
        # Verify user has access to the warehouse
        if article.magasin.entreprise_id != current_user.get('entreprise_id'):
            logger.warning(
                f"Unauthorized price lookup for article {article_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à cet article"
            )
        
        prices = await FournisseurScoringService.get_best_price(article_id)
        
        logger.info(
            f"Best price retrieved for article {article_id} "
            f"user={current_user.get('id')}"
        )
        
        return {"article_id": article_id, "prices": prices}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving best prices: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
