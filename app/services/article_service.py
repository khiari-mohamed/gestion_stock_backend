from typing import List, Optional
from prisma.models import Article
from app.core.database import prisma
from app.schemas.article import ArticleCreate, ArticleUpdate

class ArticleService:
    
    @staticmethod
    async def create_article(data: ArticleCreate) -> Article:
        return await prisma.article.create(
            data={
                "code": data.code,
                "designation": data.designation,
                "description": data.description,
                "code_barre": data.code_barre,
                "unite": data.unite,
                "prix_achat": data.prix_achat,
                "prix_vente": data.prix_vente,
                "stock_min": data.stock_min,
                "stock_max": data.stock_max,
                "date_peremption": data.date_peremption,
                "magasin_id": data.magasin_id
            }
        )
    
    @staticmethod
    async def get_article(article_id: str) -> Optional[Article]:
        return await prisma.article.find_unique(where={"id": article_id})
    
    @staticmethod
    async def get_articles_by_magasin(magasin_id: str, skip: int = 0, limit: int = 100) -> List[Article]:
        return await prisma.article.find_many(
            where={"magasin_id": magasin_id, "is_active": True},
            skip=skip,
            take=limit,
            order={"designation": "asc"}
        )
    
    @staticmethod
    async def update_article(article_id: str, data: ArticleUpdate) -> Optional[Article]:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await ArticleService.get_article(article_id)
        
        return await prisma.article.update(
            where={"id": article_id},
            data=update_data
        )
    
    @staticmethod
    async def delete_article(article_id: str) -> bool:
        await prisma.article.update(
            where={"id": article_id},
            data={"is_active": False}
        )
        return True
    
    @staticmethod
    async def get_articles_faibles(magasin_id: str) -> List[Article]:
        """Articles avec stock actuel <= stock_min"""
        articles = await prisma.article.find_many(
            where={
                "magasin_id": magasin_id,
                "is_active": True
            }
        )
        return [a for a in articles if a.stock_actuel <= a.stock_min]
    
    @staticmethod
    async def search_articles(magasin_id: str, query: str) -> List[Article]:
        return await prisma.article.find_many(
            where={
                "magasin_id": magasin_id,
                "is_active": True,
                "OR": [
                    {"code": {"contains": query, "mode": "insensitive"}},
                    {"designation": {"contains": query, "mode": "insensitive"}},
                    {"code_barre": {"contains": query, "mode": "insensitive"}}
                ]
            },
            take=50
        )
