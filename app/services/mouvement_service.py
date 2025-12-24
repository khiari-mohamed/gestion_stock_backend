from typing import List
from datetime import datetime
from prisma.models import MouvementStock, Article
from app.core.database import prisma
from app.schemas.mouvement import MouvementStockCreate

class MouvementService:
    
    @staticmethod
    async def create_mouvement(data: MouvementStockCreate) -> MouvementStock:
        # Créer le mouvement
        mouvement = await prisma.mouvementstock.create(
            data={
                "type": data.type,
                "quantite": data.quantite,
                "prix_unitaire": data.prix_unitaire,
                "motif": data.motif,
                "reference_doc": data.reference_doc,
                "date_mouvement": data.date_mouvement or datetime.now(),
                "article_id": data.article_id,
                "magasin_id": data.magasin_id,
                "fournisseur_id": data.fournisseur_id
            }
        )
        
        # Mettre à jour le stock de l'article
        await MouvementService._update_stock(data.article_id, data.type, data.quantite)
        
        return mouvement
    
    @staticmethod
    async def _update_stock(article_id: str, type_mouvement: str, quantite: int):
        article = await prisma.article.find_unique(where={"id": article_id})
        if not article:
            return
        
        if type_mouvement == "entree":
            nouveau_stock = article.stock_actuel + quantite
        elif type_mouvement == "sortie":
            nouveau_stock = max(0, article.stock_actuel - quantite)
        elif type_mouvement == "ajustement":
            nouveau_stock = quantite
        else:  # retour
            nouveau_stock = article.stock_actuel + quantite
        
        await prisma.article.update(
            where={"id": article_id},
            data={"stock_actuel": nouveau_stock}
        )
    
    @staticmethod
    async def get_mouvements_by_article(article_id: str, limit: int = 50) -> List[MouvementStock]:
        return await prisma.mouvementstock.find_many(
            where={"article_id": article_id},
            order={"date_mouvement": "desc"},
            take=limit
        )
    
    @staticmethod
    async def get_mouvements_by_magasin(
        magasin_id: str, 
        date_debut: datetime = None,
        date_fin: datetime = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MouvementStock]:
        where_clause = {"magasin_id": magasin_id}
        
        if date_debut or date_fin:
            where_clause["date_mouvement"] = {}
            if date_debut:
                where_clause["date_mouvement"]["gte"] = date_debut
            if date_fin:
                where_clause["date_mouvement"]["lte"] = date_fin
        
        return await prisma.mouvementstock.find_many(
            where=where_clause,
            skip=skip,
            take=limit,
            order={"date_mouvement": "desc"},
            include={"article": True}
        )
