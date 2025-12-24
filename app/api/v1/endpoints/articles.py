from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from app.api.v1.models.schemas import ArticleCreate, ArticleUpdate, ArticleResponse
from app.services.article_service import ArticleService
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouvel article"""
    try:
        article = await ArticleService.create_article(data)
        return article
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer un article par ID"""
    article = await ArticleService.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article

@router.get("/magasin/{magasin_id}", response_model=List[ArticleResponse])
async def get_articles_by_magasin(
    magasin_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """Lister tous les articles d'un magasin"""
    articles = await ArticleService.get_articles_by_magasin(magasin_id, skip, limit)
    return articles

@router.get("/magasin/{magasin_id}/faibles", response_model=List[ArticleResponse])
async def get_articles_faibles(
    magasin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les articles avec stock faible (stock_actuel <= stock_min)"""
    articles = await ArticleService.get_articles_faibles(magasin_id)
    return articles

@router.get("/magasin/{magasin_id}/search", response_model=List[ArticleResponse])
async def search_articles(
    magasin_id: str,
    q: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user)
):
    """Rechercher des articles par code, désignation ou code-barres"""
    articles = await ArticleService.search_articles(magasin_id, q)
    return articles

@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: str,
    data: ArticleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un article"""
    article = await ArticleService.update_article(article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article

@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer (désactiver) un article"""
    await ArticleService.delete_article(article_id)
    return None
