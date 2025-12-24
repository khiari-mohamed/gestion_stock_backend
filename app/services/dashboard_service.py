from typing import Dict
from app.core.database import prisma
from app.utils.helpers import calculate_stock_value

class DashboardService:
    
    @staticmethod
    async def get_dashboard_stats(magasin_id: str) -> Dict:
        """Récupérer les statistiques du tableau de bord pour le MVP"""
        
        # Récupérer tous les articles du magasin
        articles = await prisma.article.find_many(
            where={"magasin_id": magasin_id, "is_active": True}
        )
        
        # Convertir en dict pour calculate_stock_value
        articles_dict = [
            {
                "stock_actuel": a.stock_actuel,
                "prix_achat": a.prix_achat
            }
            for a in articles
        ]
        
        # Calculer la valeur totale du stock
        valeur_stock_total = calculate_stock_value(articles_dict)
        
        # Articles avec stock faible
        articles_faibles = [
            a for a in articles 
            if a.stock_actuel <= a.stock_min
        ]
        
        # Articles en rupture
        articles_rupture = [
            a for a in articles 
            if a.stock_actuel == 0
        ]
        
        return {
            "valeur_stock_total_dt": round(valeur_stock_total, 2),
            "total_articles": len(articles),
            "articles_faibles_count": len(articles_faibles),
            "articles_rupture_count": len(articles_rupture),
            "articles_faibles": [
                {
                    "id": a.id,
                    "code": a.code,
                    "designation": a.designation,
                    "stock_actuel": a.stock_actuel,
                    "stock_min": a.stock_min
                }
                for a in articles_faibles[:10]  # Top 10
            ]
        }
