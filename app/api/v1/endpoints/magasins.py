from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.magasin import MagasinCreate, MagasinUpdate, MagasinResponse
from app.core.database import prisma
from app.core.security import get_current_user, verify_user_access_to_magasin
from app.core.rbac import Permission, check_permission
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/magasins", tags=["Magasins"])


@router.post("/", response_model=MagasinResponse)
async def create_magasin(
    magasin: MagasinCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_MAGASIN))
):
    """Créer un nouveau magasin"""
    try:
        # Only PATRON and GERANT can create warehouses
        if current_user.get('role') not in ['PATRON', 'GERANT']:
            logger.warning(
                f"Unauthorized magasin creation by {current_user.get('role')} "
                f"user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Seul un administrateur peut créer des magasins"
            )
        
        # Générer un code unique si non fourni
        code = magasin.code
        if not code:
            count = await prisma.magasin.count(
                where={"entreprise_id": current_user.get("entreprise_id")}
            )
            code = f"MAG{count + 1:03d}"
        
        new_magasin = await prisma.magasin.create(
            data={
                "nom": magasin.nom,
                "code": code,
                "adresse": magasin.adresse,
                "ville": magasin.ville,
                "telephone": magasin.telephone,
                "is_principal": magasin.is_principal,
                "entreprise_id": current_user.get("entreprise_id")
            }
        )
        
        logger.info(
            f"Magasin created: {new_magasin.id} code={code} "
            f"user={current_user.get('id')}"
        )
        
        return new_magasin
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating magasin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[MagasinResponse])
async def list_magasins(
    current_user: dict = Depends(check_permission(Permission.READ_MAGASIN))
):
    """Lister tous les magasins de l'entreprise"""
    try:
        magasins = await prisma.magasin.find_many(
            where={"entreprise_id": current_user.get("entreprise_id")}
        )
        
        logger.info(
            f"Magasins list retrieved for enterprise {current_user.get('entreprise_id')} "
            f"user={current_user.get('id')} count={len(magasins)}"
        )
        
        return magasins
    
    except Exception as e:
        logger.error(f"Error retrieving magasins: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{magasin_id}", response_model=MagasinResponse)
async def get_magasin(
    magasin_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_MAGASIN))
):
    """Récupérer un magasin par ID"""
    try:
        magasin = await prisma.magasin.find_unique(where={"id": magasin_id})
        
        if not magasin:
            raise HTTPException(status_code=404, detail="Magasin non trouvé")
        
        # Verify user has access to this warehouse
        if magasin.entreprise_id != current_user.get("entreprise_id"):
            logger.warning(
                f"Unauthorized magasin access {magasin_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        logger.info(f"Magasin retrieved: {magasin_id} user={current_user.get('id')}")
        
        return magasin
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving magasin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{magasin_id}", response_model=MagasinResponse)
async def update_magasin(
    magasin_id: str,
    magasin: MagasinUpdate,
    current_user: dict = Depends(check_permission(Permission.UPDATE_MAGASIN))
):
    """Mettre à jour un magasin"""
    try:
        existing = await prisma.magasin.find_unique(where={"id": magasin_id})
        
        if not existing:
            raise HTTPException(status_code=404, detail="Magasin non trouvé")
        
        # Verify user has access to this warehouse
        if existing.entreprise_id != current_user.get("entreprise_id"):
            logger.warning(
                f"Unauthorized magasin update {magasin_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        updated = await prisma.magasin.update(
            where={"id": magasin_id},
            data=magasin.dict(exclude_unset=True)
        )
        
        logger.info(
            f"Magasin updated: {magasin_id} "
            f"user={current_user.get('id')}"
        )
        
        return updated
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating magasin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{magasin_id}", status_code=204)
async def delete_magasin(
    magasin_id: str,
    current_user: dict = Depends(check_permission(Permission.DELETE_MAGASIN))
):
    """Supprimer un magasin (seulement PATRON)"""
    try:
        # Only PATRON can delete warehouses
        if current_user.get('role') != 'PATRON':
            logger.warning(
                f"Unauthorized magasin deletion {magasin_id} "
                f"by {current_user.get('role')} user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Seul le propriétaire peut supprimer des magasins"
            )
        
        existing = await prisma.magasin.find_unique(where={"id": magasin_id})
        
        if not existing:
            raise HTTPException(status_code=404, detail="Magasin non trouvé")
        
        # Verify user has access to this warehouse
        if existing.entreprise_id != current_user.get("entreprise_id"):
            logger.warning(
                f"Unauthorized magasin deletion {magasin_id} "
                f"by user {current_user.get('id')}"
            )
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        await prisma.magasin.delete(where={"id": magasin_id})
        
        logger.info(
            f"Magasin deleted: {magasin_id} "
            f"user={current_user.get('id')} role={current_user.get('role')}"
        )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting magasin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
