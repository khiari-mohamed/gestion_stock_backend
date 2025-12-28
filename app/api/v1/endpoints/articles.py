from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from app.api.v1.models.schemas import ArticleCreate, ArticleUpdate, ArticleResponse
from app.services.article_service import ArticleService
from app.core.security import get_current_user, verify_user_access_to_magasin
from app.core.rbac import Permission, check_permission
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    current_user: dict = Depends(check_permission(Permission.CREATE_ARTICLE))
):
    """
    Create new article
    
    Only users with CREATE_ARTICLE permission can access this.
    Article will be created in the warehouse of the authenticated user's enterprise.
    """
    try:
        # Verify user has access to warehouse
        if not await verify_user_access_to_magasin(current_user, data.magasin_id):
            logger.warning(
                f"User {current_user['id']} attempted to create article in unauthorized warehouse"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce magasin"
            )
        
        article = await ArticleService.create_article(data, current_user)
        
        logger.info(f"Article created: {article.id} by user {current_user['id']}")
        
        return article
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la création de l'article"
        )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_ARTICLE))
):
    """
    Get article by ID
    
    User can only access articles from their enterprise warehouses
    """
    article = await ArticleService.get_article(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    # Verify multi-tenant isolation
    if article.magasin.entreprise_id != current_user["entreprise_id"]:
        logger.warning(
            f"User {current_user['id']} attempted unauthorized access to article {article_id}"
        )
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    return article


@router.get("/magasin/{magasin_id}", response_model=List[ArticleResponse])
async def get_articles_by_magasin(
    magasin_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(check_permission(Permission.READ_ARTICLE))
):
    """
    List all articles in a warehouse
    
    Paginated results with multi-tenant isolation
    """
    # Verify user has access to warehouse
    if not await verify_user_access_to_magasin(current_user, magasin_id):
        logger.warning(
            f"User {current_user['id']} attempted to list articles from unauthorized warehouse"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce magasin"
        )
    
    articles = await ArticleService.get_articles_by_magasin(magasin_id, skip, limit)
    return articles


@router.get("/magasin/{magasin_id}/faibles", response_model=List[ArticleResponse])
async def get_articles_faibles(
    magasin_id: str,
    current_user: dict = Depends(check_permission(Permission.READ_ARTICLE))
):
    """
    Get articles with low stock levels
    
    Returns articles where stock_actuel <= stock_min
    """
    # Verify access
    if not await verify_user_access_to_magasin(current_user, magasin_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )
    
    articles = await ArticleService.get_articles_faibles(magasin_id)
    return articles


@router.get("/magasin/{magasin_id}/search", response_model=List[ArticleResponse])
async def search_articles(
    magasin_id: str,
    q: str = Query(..., min_length=1),
    current_user: dict = Depends(check_permission(Permission.READ_ARTICLE))
):
    """
    Search articles by code, designation or barcode
    """
    # Verify access
    if not await verify_user_access_to_magasin(current_user, magasin_id):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    articles = await ArticleService.search_articles(magasin_id, q)
    return articles


@router.get("/scan/{code_barre}", response_model=ArticleResponse)
async def scan_article(
    code_barre: str,
    magasin_id: str = Query(...),
    current_user: dict = Depends(check_permission(Permission.READ_ARTICLE))
):
    """
    Scan barcode and retrieve article
    
    Used for mobile quick lookup
    """
    # Verify access
    if not await verify_user_access_to_magasin(current_user, magasin_id):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    article = await ArticleService.get_by_barcode(code_barre, magasin_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: str,
    data: ArticleUpdate,
    current_user: dict = Depends(check_permission(Permission.UPDATE_ARTICLE))
):
    """
    Update article
    
    Only users with UPDATE_ARTICLE permission can access this
    """
    try:
        # Verify access
        article = await ArticleService.get_article(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article non trouvé")
        
        if article.magasin.entreprise_id != current_user["entreprise_id"]:
            logger.warning(
                f"User {current_user['id']} attempted to update unauthorized article {article_id}"
            )
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        updated_article = await ArticleService.update_article(article_id, data)
        
        logger.info(f"Article updated: {article_id} by user {current_user['id']}")
        
        return updated_article
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la mise à jour"
        )


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: str,
    current_user: dict = Depends(check_permission(Permission.DELETE_ARTICLE))
):
    """
    Delete (soft delete) article
    
    Only PATRON and GERANT roles can delete articles
    """
    try:
        # Additional role check for deletion
        if current_user["role"].upper() not in ["PATRON", "GERANT"]:
            logger.warning(
                f"User {current_user['id']} (role: {current_user['role']}) attempted to delete article"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les patrons et gérants peuvent supprimer des articles"
            )
        
        # Verify access
        article = await ArticleService.get_article(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article non trouvé")
        
        if article.magasin.entreprise_id != current_user["entreprise_id"]:
            logger.warning(
                f"User {current_user['id']} attempted to delete unauthorized article"
            )
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        await ArticleService.delete_article(article_id)
        
        logger.info(f"Article deleted: {article_id} by user {current_user['id']}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de la suppression"
        )

